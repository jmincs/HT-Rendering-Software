from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
import os
import h5py
import json
import psutil
import shutil
from django.conf import settings
import subprocess
from .process_tcf import ReadLDMTCFHT_10, set_progress, generate_images, set_num_frames, ReadLDMTCFFL_10, remove_background
from .models import ProcessedFile, StagedFile
from skimage.transform import resize

last_valid_progress = 0.0

def get_progress():
    global last_valid_progress
    if os.path.exists('media/progress.txt'):
        with open('media/progress.txt', 'r') as f:
            progress = f.read().strip()
            if progress == '':
                return last_valid_progress
            try:
                progress_value = float(progress)
                last_valid_progress = progress_value
                return progress_value
            except ValueError:
                return last_valid_progress
    return 0.0

def event_stream():
    while True:
        progress_data = {'percent_complete': get_progress()}
        yield f"data: {json.dumps(progress_data)}\n\n"

@csrf_exempt
def progress_sse(request):
    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    return response

def home(request):
    return HttpResponse("Welcome to the File Upload API! Navigate to /api/upload/ to upload files.")

@csrf_exempt
def upload_file(request):
    set_progress(0.0)
    tcf_file = request.FILES['file']
    processed_file = ProcessedFile.objects.create(
        name=tcf_file.name,
        size=tcf_file.size / 1024.0,  # Convert to KB
    )
    tcf_file_name = tcf_file.name

    # Save the .tcf file in media/uploads/
    tcf_upload_path = os.path.join(settings.MEDIA_ROOT, 'uploads', tcf_file_name)
    with open(tcf_upload_path, 'wb+') as destination:
        for chunk in tcf_file.chunks():
            destination.write(chunk)

    # Create a folder within media/textures/
    texture_folder_name = os.path.splitext(tcf_file_name)[0] + '-textures'
    texture_folder_path = os.path.join(settings.MEDIA_ROOT, 'textures', texture_folder_name)

    if not os.path.exists(texture_folder_path):
        os.makedirs(texture_folder_path)

    # Process the .tcf file to generate .tga files
    with h5py.File(tcf_upload_path, 'r') as file:
        data_3d = file['Data/3D']
        num_frames = len(list(data_3d.keys()))
        set_num_frames(num_frames)
        flattened_data = []

        for frame in range(num_frames):
            HT_Data = remove_background(ReadLDMTCFHT_10(file, frame))
            FL_Data = ReadLDMTCFFL_10(file, frame)
            FL_Data = resize(FL_Data, (HT_Data.shape[0], HT_Data.shape[0], 20), order=1, anti_aliasing=True, preserve_range=True)
            print("HT_Data min, max:", HT_Data.min(), HT_Data.max())
            print("FL_Data min, max:", FL_Data.min(), FL_Data.max())
            generate_images(HT_Data, FL_Data, frame, texture_folder_path)
            # data, _ = ReadLDMTCFHT_10(file, timeFrameIndex=frame)  # Adjust timeFrameIndex as needed
            # flattened_data.extend(data)
            # generate_images(data, frame_num=frame, output_dir=texture_folder_path)
            set_progress(((frame + 1) / num_frames) * 100)
    
    set_progress(0.0)
    return JsonResponse({'message': 'TCF uploaded and textures saved.'})


@csrf_exempt
def delete_file(request):
    data = json.loads(request.body)
    file_name = data.get('file_name')

    # Define file paths
    upload_directory = 'media/uploads/'
    textures_directory = 'media/textures/'
    tcf_file_path = os.path.join(upload_directory, file_name)
    parent_path = os.path.dirname(os.path.dirname(settings.MEDIA_ROOT))
    data_path = os.path.join(parent_path, 'Windows', 'Data')

    texture_folder_name = os.path.splitext(file_name)[0] + '-textures'
    texture_folder_path = os.path.join(textures_directory, texture_folder_name)
    
    # Delete all matching records from the database
    processed_files = ProcessedFile.objects.filter(name=file_name)
    processed_files.delete()

    # Delete the TCF file
    if os.path.exists(tcf_file_path):
        os.remove(tcf_file_path)
    else:
        return JsonResponse({'status': 'error', 'message': 'TCF file not found!'})

    # Delete the corresponding texture folder if it exists
    if os.path.exists(texture_folder_path):
        # Remove all files inside the folder first
        for root, dirs, files in os.walk(texture_folder_path, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for directory in dirs:
                os.rmdir(os.path.join(root, directory))

        # Remove the empty folder
        os.rmdir(texture_folder_path)

    # Check if the file is staged
    if StagedFile.objects.filter(tcf_file_name=file_name).exists():
        # Clear out the media/staged/ directory
        if os.path.exists(data_path):
            # Remove all files inside the folder first
            for root, dirs, files in os.walk(data_path, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for directory in dirs:
                    os.rmdir(os.path.join(root, directory))
    
        StagedFile.objects.filter(tcf_file_name=file_name).delete()
        
    return JsonResponse({'status': 'success'})
    

def get_processed_files(request):
    files = ProcessedFile.objects.all().values('name', 'size', 'date_processed')
    files_list = list(files)
    return JsonResponse(files_list, safe=False)

@csrf_exempt
def stage_files(request):
    data = json.loads(request.body)
    file_name = data.get('file_name')
    parent_path = os.path.dirname(os.path.dirname(settings.MEDIA_ROOT))
    data_path = os.path.join(parent_path, 'Windows', 'Data')

    # Define the source and destination directories
    texture_folder_name = os.path.splitext(file_name)[0] + '-textures'
    texture_folder_path = os.path.join(settings.MEDIA_ROOT, 'textures', texture_folder_name)

    if os.path.exists(data_path):
        shutil.rmtree(data_path)
    os.makedirs(data_path)

    # Copy .tga files from textures folder to staged folder with replacement
    for file in os.listdir(texture_folder_path):
        src_file = os.path.join(texture_folder_path, file)
        dst_file = os.path.join(data_path, file)
        shutil.copy2(src_file, dst_file)  # Copy and replace if it exists
        
    StagedFile.objects.get_or_create(tcf_file_name=file_name)
    
    return JsonResponse({'status': 'success'})
@csrf_exempt
def stop_pixel_streaming(request):
    # Stop the Unreal Engine Pixel Streaming process
    if is_process_running('NiagaraPointCloud.exe'):
        subprocess.run(["taskkill", "/F", "/IM", "NiagaraPointCloud.exe"], check=True)
    # Stop the Node.js process related to Pixel Streaming server
    return JsonResponse({"status": "success", "message": "Pixel Streaming server stopped successfully."})

@csrf_exempt
def start_unreal_play(request):
    # Define paths
    parent_path = os.path.dirname(os.path.dirname(settings.MEDIA_ROOT))
    
    pixel_streaming_script = os.path.join(parent_path, 'Windows', 'NiagaraPointCloud', 'Samples', 'PixelStreaming', 'WebServers', 'SignallingWebServer', 'platform_scripts', 'cmd', 'run_local.bat')
    unreal_exe = os.path.join(parent_path, 'Windows', 'NiagaraPointCloud.exe')

    if is_process_running('NiagaraPointCloud.exe'):
        subprocess.run(["taskkill", "/F", "/IM", "NiagaraPointCloud.exe"], check=True)
    
    # Run the Pixel Streaming server
    subprocess.Popen(["cmd.exe", "/c", pixel_streaming_script], shell=True)

    # Run the Unreal Engine executable
    subprocess.Popen([unreal_exe, "-PixelStreamingIP=localhost", "-PixelStreamingPort=8888"], shell=True)
    
    return JsonResponse({"status": "success", "message": "Unreal Engine play started successfully."})


def is_process_running(process_name):
    try:
        # Run 'tasklist' and search for the process name
        result = subprocess.run(['tasklist'], capture_output=True, text=True)
        return process_name in result.stdout
    except Exception as e:
        print(f"Error checking process: {e}")
        return False
    
@csrf_exempt
def delete_files(request):
    parent_path = os.path.dirname(os.path.dirname(settings.MEDIA_ROOT))
    data_path = os.path.join(parent_path, 'Windows', 'Data')
    shutil.rmtree(data_path)

    return JsonResponse({'status': 'success'})

@csrf_exempt
def check_unreal_status(request):
    if is_process_running('NiagaraPointCloud.exe'):
        return JsonResponse({"status": "running"})
    else:
        return JsonResponse({"status": "not_running"})
    
def is_process_running(process_name):
    for proc in psutil.process_iter():
        try:
            if process_name.lower() in proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False