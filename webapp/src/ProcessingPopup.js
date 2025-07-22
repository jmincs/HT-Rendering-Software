import React from 'react';

const ProcessingPopup = ({ progress, message, isFileProcessed, onFileInput, onClose }) => {
    let displayMessage;
    if (progress === 100) {
      displayMessage = 'File processing complete!';
    } else if (progress > 0 && progress < 100) {
      displayMessage = 'Processing...';
    } else {
      displayMessage = message; 
    }
  
    return (
      <div className="popup-overlay">
        <div className="popup-content">
          {progress === 0 && (
            <button className="close-button" onClick={onClose}>×</button>
          )}
          <h3>Import and Process File</h3>
          {progress === 0 ? (
            <>
              <input type="file" onChange={onFileInput} />
              {message && <p>{message}</p>}
            </>
          ) : (
            <>
              <p>{displayMessage}</p>
              <progress value={progress} max="100"></progress>
              <p>{progress}%</p>
  
              {isFileProcessed && (
                <button onClick={onClose}>Done</button>
              )}
            </>
          )}
        </div>
      </div>
    );
  };
  
  export default ProcessingPopup;
