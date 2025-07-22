import React from 'react';

const DeletePopup = ({ fileName, onDeleteConfirm, onCancel }) => {
  return (
    <div className="popup-overlay">
      <div className="popup-content">
        <h3>Confirm Deletion</h3>
        <p className="file-name">Are you sure you want to delete {fileName}?</p>
        <div className="popup-buttons">
          <button className="confirm-btn" onClick={onDeleteConfirm}>
            Yes
          </button>
          <button className="cancel-btn" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeletePopup;
