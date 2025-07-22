import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import ProcessingPopup from './ProcessingPopup';
import DeletePopup from './DeletePopup';  
import StagePopup from './StagePopup';  
import UnstagePopup from './UnstagePopup';

function App() {
  const [message, setMessage] = useState('');
  const [messageColor, setMessageColor] = useState('red');
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [eventSource, setEventSource] = useState(null);
  const [progressLocked, setProgressLocked] = useState(false);
  const [processedFiles, setProcessedFiles] = useState([]);
  const [showPopup, setShowPopup] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [showDeletePopup, setShowDeletePopup] = useState(false);
  const [fileToDelete, setFileToDelete] = useState(null);
  const [showStagePopup, setShowStagePopup] = useState(false);  
  const [fileToStage, setFileToStage] = useState(null);  
  const [stagedFile, setStagedFile] = useState(null);  
  const [isFileProcessed, setIsFileProcessed] = useState(false);
  const [showUnstagePopup, setShowUnstagePopup] = useState(false);
  const [fileToUnstage, setFileToUnstage] = useState(null);
  

  const resetState = () => {
    setMessage('');
    setMessageColor('red');
    setFile(null);
    setProgress(0);
    setProgressLocked(false);
    setStatusMessage('');

    if (eventSource) {
      eventSource.close();
      setEventSource(null);
    }
  };

  useEffect(() => {
    const storedFiles = JSON.parse(localStorage.getItem('processedFiles')) || [];
    setProcessedFiles(storedFiles);
    const storedStagedFile = localStorage.getItem('stagedFile');
    if (storedStagedFile) {
        setStagedFile(storedStagedFile);
    }
    if (file) {
      const es = new EventSource('http://localhost:8000/api/progress_sse/');
      es.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (!progressLocked) {
          if (data.percent_complete < 100) {
            setProgress(data.percent_complete);
          } else {
            setProgress(100);
            setProgressLocked(true);
            setMessageColor('green');
          }
        }
      };

      setEventSource(es);
      return () => {
        if (es) {
          es.close();
        }
      };
    }
  }, [file, progressLocked]);

  const handleFileInput = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      if (selectedFile.name.endsWith('.TCF')) {
        resetState();
        setProgress(0);
        setProgressLocked(false);
        setFile(selectedFile);
        setIsFileProcessed(false);
        uploadFile(selectedFile);
      } else {
        setStatusMessage('Error: Please select a file with a .TCF extension.');
      }
    }
  };

  const uploadFile = async (file) => {
    setMessageColor('Green');
    setStatusMessage('Transferring to backend...');
    const formData = new FormData();
    formData.append('file', file);
    await axios.post('http://localhost:8000/api/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob',
    });

    const newFile = {
      name: file.name,
      size: (file.size / 1024).toFixed(2),
      date: new Date().toLocaleDateString(),
      url: window.URL.createObjectURL(file),
    };

    setProcessedFiles((prevFiles) => {
      const updatedFiles = [...prevFiles, newFile];
      localStorage.setItem('processedFiles', JSON.stringify(updatedFiles));
      return updatedFiles;
    });
    setIsFileProcessed(true);
  };

  const handleDelete = (fileName) => {
    setFileToDelete(fileName);
    setShowDeletePopup(true);
  };

  const handleDeleteConfirm = async () => {
    const response = await axios.post('http://localhost:8000/api/delete/', { file_name: fileToDelete });
    if (response.data.status === 'success') {
      setProcessedFiles((prevFiles) => {
        const updatedFiles = prevFiles.filter(file => file.name !== fileToDelete);
        localStorage.setItem('processedFiles', JSON.stringify(updatedFiles));
        return updatedFiles;
      });
      if (stagedFile === fileToDelete) {
        setStagedFile(null);  
        localStorage.removeItem('stagedFile');
            
        try {
          await axios.post('http://localhost:8000/api/stop_pixel_streaming/'); 
          console.log('Pixel Streaming server stopped.');
        } catch (error) {
          console.error('Failed to stop Pixel Streaming server:', error);
        }
      }
    } else {
      alert(`Error: ${response.data.message}`);
    }
    setShowDeletePopup(false);
    setFileToDelete(null);
  };

  const handleDeleteCancel = () => {
    setShowDeletePopup(false);
    setFileToDelete(null);
  };

  const handleOpenPopup = () => {
    resetState();
    setShowPopup(true);
  };

  const handleStageFiles = (fileName) => {
    if (stagedFile === fileName){
      setFileToUnstage(fileName);
      setShowUnstagePopup(true);
    }
    else{
      setFileToStage(fileName); 
      setShowStagePopup(true);    
    }

  };
  
  const handleUnstageConfirm = async () => {
    await axios.post('http://localhost:8000/api/unstage_files/', { file_name: fileToUnstage });
  
    setStagedFile(null);
    localStorage.removeItem('stagedFile');
    setShowUnstagePopup(false);  
    setFileToUnstage(null);
  
    await axios.post('http://localhost:8000/api/stop_pixel_streaming/');
    window.location.href = 'http://localhost:3000/';
    window.location.reload();
  };

  const handleStageConfirm = async () => {
    await axios.post('http://localhost:8000/api/stage/', { file_name: fileToStage });

    setStagedFile(fileToStage);
    localStorage.setItem('stagedFile', fileToStage);
    setShowStagePopup(false);  
    setFileToStage(null);      
    await axios.post('http://localhost:8000/api/start_unreal_play/');


    const interval = setInterval(async () => {
      try {
          const response = await axios.get('http://localhost:8000/api/check_unreal_status/');
          if (response.data.status === 'running') {
              clearInterval(interval);  // Stop polling once Unreal is confirmed to be running
              setTimeout(() => {
                window.location.href = 'http://localhost:3000/';
                window.location.reload();
              }, 2000); // 2-second delay
          }
      } catch (error) {
          console.error('Error checking Unreal status:', error);
      }
  }, 1000);  // Poll every 2 seconds
  };

  const handleStageCancel = () => {
    setShowStagePopup(false);  
    setFileToStage(null);
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="button-container">
          <button onClick={handleOpenPopup}>Import TCF File</button>
          
          {message && (
            <p className="message" style={{ color: messageColor }}>
              {message}
            </p>
          )}
        </div>
        <div className="pixel-streaming-label">
          <h2>Pixel Streaming</h2>
        </div>
        <div 
          className="pixel-streaming-container" 
          style={{ 
            width: '40vw',  
            height: '45vh', 
            overflow: 'hidden', 
            position: 'absolute', 
            bottom: '50px',  
            left: '3%',  
            zIndex: '100',  
          }}
        >
          <iframe
            src="http://localhost:80"
            title="Pixel Streaming"
            width="100%"
            height="100%"  
            style={{ 
              border: 'none', 
              position: 'absolute', 
              left: '0',
            }}
            allowFullScreen
          />
        </div>
        <div className="scrollable-container">
          <h2 className="table-header">Processed TCF Files</h2>
          <div className="table-wrapper">
            <div className="table-headers">
              <table>
                <thead>
                  <tr>
                    <th>File Name</th>
                    <th>Size (KB)</th>
                    <th>Date Processed</th>
                    <th>Action</th>
                  </tr>
                </thead>
              </table>
            </div>
            <div className="table-body-container">
              <table>
                <tbody>
                  {processedFiles.map((file, index) => (
                    <tr key={index}>
                      <td>{file.name}</td>
                      <td>{file.size}</td>
                      <td>{file.date}</td>
                      <td>
                        <button 
                          onClick={() => handleDelete(file.name)} className="delete-button">
                          Delete
                        </button>
                        <button 
                          onClick={() => handleStageFiles(file.name)} 
                          className={stagedFile === file.name ? "staged-button" : "stage-button"}>
                          {stagedFile === file.name ? "Staged" : "Stage"}
                        </button>  
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </header>

      {showPopup && (
        <ProcessingPopup
          progress={progress}
          message={statusMessage}
          isFileProcessed={isFileProcessed}
          onFileInput={handleFileInput}
          onClose={() => {
            resetState();
            setShowPopup(false);
            setIsFileProcessed(false);
          }}
        />
      )}

      {showDeletePopup && (
        <DeletePopup
          fileName={fileToDelete}
          onDeleteConfirm={handleDeleteConfirm}
          onCancel={handleDeleteCancel}
        />
      )}

      {showStagePopup && (
        <StagePopup
          fileName={fileToStage}
          onStageConfirm={handleStageConfirm}
          onCancel={handleStageCancel}
        />
      )}
      {showUnstagePopup && (
        <UnstagePopup
          fileName={fileToUnstage}
          onUnstageConfirm={handleUnstageConfirm}
          onCancel={() => {
            setShowUnstagePopup(false);
            setFileToUnstage(null);
          }}
        />
      )}
    </div>
  );
}

export default App;