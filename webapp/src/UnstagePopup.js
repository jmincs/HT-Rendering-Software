import React from 'react';

function UnstagePopup({ fileName, onUnstageConfirm, onCancel }) {
  return (
    <div className="popup-overlay">
      <div className="popup-content">
        <h3>Unstage File</h3>
        <p>Are you sure you want to unstage this file?</p>
        <button onClick={onUnstageConfirm}>Yes</button>
        <button onClick={onCancel}>Cancel</button>
      </div>
    </div>
  );
}

export default UnstagePopup;
