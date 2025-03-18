document.addEventListener('DOMContentLoaded', function() {
  const apiKeyInput = document.getElementById('api-key');
  const saveApiKeyBtn = document.getElementById('save-api-key');
  const apiModeRadio = document.getElementById('api-mode');
  const localModeRadio = document.getElementById('local-mode');
  const copyModeRadio = document.getElementById('copy-mode');
  const extractSingleBtn = document.getElementById('extract-single');
  const extractAllBtn = document.getElementById('extract-all');
  const statusMessage = document.getElementById('status-message');

  // Load saved settings
  chrome.storage.sync.get(['apiKey', 'mode'], function(result) {
    if (result.apiKey) {
      apiKeyInput.value = result.apiKey;
      showStatus('API key loaded', 'success');
    }
    
    if (result.mode) {
      if (result.mode === 'copy') {
        copyModeRadio.checked = true;
      } else if (result.mode === 'api') {
        apiModeRadio.checked = true;
      } else {
        localModeRadio.checked = true;
      }
    }
  });

  // Save API key
  saveApiKeyBtn.addEventListener('click', function() {
    const apiKey = apiKeyInput.value.trim();
    if (apiKey) {
      chrome.storage.sync.set({apiKey: apiKey}, function() {
        showStatus('API key saved', 'success');
      });
    } else {
      showStatus('Please enter a valid API key', 'error');
    }
  });

  // Save mode selection
  apiModeRadio.addEventListener('change', function() {
    if (this.checked) {
      chrome.storage.sync.set({mode: 'api'});
    }
  });

  copyModeRadio.addEventListener('change', function() {
    if (this.checked) {
      chrome.storage.sync.set({mode: 'copy'});
    }
  });

  localModeRadio.addEventListener('change', function() {
    if (this.checked) {
      chrome.storage.sync.set({mode: 'local'});
    }
  });

  // Extract current question button
  extractSingleBtn.addEventListener('click', function() {
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      // Send message directly to background script
      chrome.runtime.sendMessage({
        action: 'extractCurrentQuestion', 
        tabId: tabs[0].id
      }, function(response) {
        if (chrome.runtime.lastError) {
          showStatus('Error: ' + chrome.runtime.lastError.message, 'error');
          return;
        }
        
        if (response && response.success) {
          showStatus('Current question extracted', 'success');
        } else {
          showStatus('Failed to extract question: ' + (response ? response.error : 'Unknown error'), 'error');
        }
      });
    });
  });

  // Extract all questions button
  extractAllBtn.addEventListener('click', function() {
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      // Send message directly to background script
      chrome.runtime.sendMessage({
        action: 'extractAllQuestions',
        tabId: tabs[0].id
      }, function(response) {
        if (chrome.runtime.lastError) {
          showStatus('Error: ' + chrome.runtime.lastError.message, 'error');
          return;
        }
        
        if (response && response.success) {
          showStatus('All questions extracted', 'success');
        } else {
          showStatus('Failed to extract questions: ' + (response ? response.error : 'Unknown error'), 'error');
        }
      });
    });
  });

  function showStatus(message, type) {
    statusMessage.textContent = message;
    statusMessage.className = type;
    
    // Clear the message after 3 seconds
    setTimeout(() => {
      statusMessage.textContent = '';
      statusMessage.className = '';
    }, 3000);
  }
});