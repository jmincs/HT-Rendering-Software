import React from 'react';

const StagePopup = ({ onStageConfirm, onCancel }) => {
  return (
    <div className="popup-overlay">
      <div className="popup-content">
        <h3>Confirm Staging</h3>
        <p>Are you sure you want to stage this file to Unreal Engine?</p>
        <div className="popup-buttons">
          <button className="confirm-btn" onClick={onStageConfirm}>
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

export default StagePopup;
