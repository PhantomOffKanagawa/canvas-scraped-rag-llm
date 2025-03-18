// Get URL parameters
const urlParams = new URLSearchParams(window.location.search);
const action = urlParams.get('action');
const id = urlParams.get('id');

// Elements
const contentContainer = document.getElementById('content-container');
const resultsSubtitle = document.getElementById('results-subtitle');

// Add a global state object to track context expansion status
const state = {
  expandedContexts: {} // Maps context IDs to their expansion state (true = expanded)
};

document.addEventListener('DOMContentLoaded', function() {
  if (action === 'loading') {
    showLoading(urlParams.get('message') || 'Processing question...');
  }
  else if (action === 'error') {
    showError(urlParams.get('title') || 'Error', urlParams.get('message') || 'An unknown error occurred.');
  }
  else if (action === 'info') {
    showInfo(urlParams.get('title') || 'Information', urlParams.get('message') || '');
  }
  else if (action === 'answer' && id) {
    // Request the answer data from background script
    chrome.runtime.sendMessage({ 
      action: 'getAnswerData', 
      id: id 
    }, function(response) {
      if (chrome.runtime.lastError || !response || !response.success) {
        showError('Error', chrome.runtime.lastError?.message || response?.error || 'Failed to get answer data');
        return;
      }
      
      showAnswer(response.data);
    });
  }
  else {
    showError('Invalid Request', 'Missing required parameters.');
  }
});

// Update UI when receiving messages from background script
chrome.runtime.onMessage.addListener(function(message, sender, sendResponse) {
  if (message.action === 'updateLoading' && message.id === id) {
    showLoading(message.message, message.data);
    sendResponse({success: true});
  }
  else if (message.action === 'showAnswer' && message.id === id) {
    showAnswer(message.data);
    sendResponse({success: true});
  }
  else if (message.action === 'showError' && message.id === id) {
    showError(message.title, message.message);
    sendResponse({success: true});
  }
  else if (message.action === 'showInfo' && message.id === id) {
    showInfo(message.title, message.message);
    sendResponse({success: true});
  }
});

// Show loading UI
function showLoading(message, data = null) {
  if (data) {
    showAnswer(data);
    // contentContainer.innerHTML = `
    //   <div class="loading-container">
    //     <p>${escapeHtml(message)}</p>
    //   </div>
    //   ${contentContainer.innerHTML}
    // `;

    // attachContextToggleListeners();

  } else {
    contentContainer.innerHTML = `
      <div class="loading-container">
        <div class="loading-spinner"></div>
        <p>${escapeHtml('Loading...')}</p>
      </div>
    `;
  }
  resultsSubtitle.textContent = escapeHtml(message);
  document.title = `Loading - Canvas Quiz Helper`;
}

// Show error UI
function showError(title, message) {
  contentContainer.innerHTML = `
    <div class="error-container">
      <h2>${escapeHtml(title)}</h2>
      <p>${escapeHtml(message)}</p>
    </div>
  `;
  resultsSubtitle.textContent = escapeHtml(title);
  document.title = `Error - Canvas Quiz Helper`;
}

// Show info message
function showInfo(title, message) {
  contentContainer.innerHTML = `
    <div class="info-container">
      <h2>${escapeHtml(title)}</h2>
      <p>${escapeHtml(message)}</p>
    </div>
  `;
  resultsSubtitle.textContent = escapeHtml(title);
  document.title = `${escapeHtml(title)} - Canvas Quiz Helper`;
}

// Show answer UI
function showAnswer(data) {
  // If it's a single question response
  if (data.question) {
    contentContainer.innerHTML = buildQuestionHtml(data.question, data.answer, data["context"] || []);
    resultsSubtitle.textContent = escapeHtml(data.question.number || 'Question');
    document.title = `${escapeHtml(data.question.number || 'Question')} - Canvas Quiz Helper`;
    attachContextToggleListeners(); // Attach listeners and restore states
  } 
  // If it's multiple questions
  else if (data.questions && Array.isArray(data.questions)) {
    const questionsHtml = data.questions.map((q, i) => {
      return buildQuestionHtml(q.question, q.answer, q['context'] || [], i);
    }).join('');
    contentContainer.innerHTML = questionsHtml;
    resultsSubtitle.textContent = `${data.questions.length} Questions`;
    document.title = `${data.questions.length} Questions - Canvas Quiz Helper`;
    attachContextToggleListeners(); // Attach listeners and restore states
  }
  // Invalid data format
  else {
    showError('Invalid Data', 'Received invalid question data format.');
  }
}

// Function to attach event listeners to context headers
function attachContextToggleListeners() {
  const contextHeaders = document.querySelectorAll('.context-header');
  contextHeaders.forEach(header => {
    const contextId = header.getAttribute('data-context-id');
    header.addEventListener('click', () => toggleContext(contextId));
  });
  applyContextExpansionStates(); // Restore expanded states
}

// Apply current expansion states to all contexts in the DOM
function applyContextExpansionStates() {
  for (const contextId in state.expandedContexts) {
    const isExpanded = state.expandedContexts[contextId];
    const contextElement = document.getElementById(`context-${contextId}`);
    const toggleText = document.getElementById(`toggle-text-${contextId}`);
    if (contextElement && toggleText) {
      contextElement.style.display = isExpanded ? 'block' : 'none';
      toggleText.textContent = isExpanded ? 'Hide' : 'Show';
    }
  }
}

// Build HTML for a question and its answer
function buildQuestionHtml(question, answer, context = [], questionIndex = 0) {
  let html = `
    <div class="question-container">
      <div class="question-title">${escapeHtml(question.number || 'Question')}</div>
      <div class="question-text">
        <h3>Question:</h3>
        <div>${escapeHtml(question.text)}</div>
      </div>
  `;
  
  // Add answer choices if present
  if (question.answers && question.answers.length > 0) {
    html += `<div class="answer-choices"><h3>Answer Choices:</h3>`;
    
    question.answers.forEach((choice, i) => {
      const letter = String.fromCharCode(65 + i);
      html += `<div class="answer-choice"><strong>${letter})</strong> ${escapeHtml(choice)}</div>`;
    });
    
    html += `</div>`;
  }
  
  // Add AI answer
  html += `
      <div class="ai-answer">
        <h3>AI Answer:</h3>
        <div>${formatAnswer(answer)}</div>
      </div>
  `;

  // Add a single collapsible card for all contexts if present
  if (context.length > 0) {
    const contextId = `q${questionIndex}-all-contexts`; // Unique ID for the combined context
    html += `
      <div class="context-container">
        <h3>Context Available:</h3>
        <div class="context-card">
          <div class="context-header" data-context-id="${contextId}">
            <span>All Contexts</span>
            <span class="context-toggle" id="toggle-text-${contextId}">Show</span>
          </div>
          <div class="context-content" id="context-${contextId}">
    `;
    context.forEach((ctx, index) => {
      html += `
        <div class="individual-context">
          <h4>Context #${index + 1}</h4>
          <div>${escapeHtml(ctx)}</div>
        </div>
      `;
    });
    html += `
          </div>
        </div>
      </div>
    `;
  }

  html += `
    </div>
  `;

  return html;
}

// Format answer text with line breaks, bold formatting, and bullet points
function formatAnswer(text) {
  if (!text) return '';

  // Escape HTML to prevent XSS
  let formattedText = escapeHtml(text);

  // Handle bullet points that may include bold formatting like **- Text**
  formattedText = formattedText.replace(/\*\*- (.*?)\*\*/g, '<li><strong>$1</strong></li>');

  // Replace markdown-style bold (**text**) with HTML bold tags, including multi-line bold
  formattedText = formattedText.replace(/\*\*([\s\S]*?)\*\*/g, '<strong>$1</strong>');

  // Replace markdown-style bullet points with HTML list items
  formattedText = formattedText.replace(/(?:^|\n)- (.*?)(?=\n|$)/g, '<li>$1</li>');

  // Wrap bullet points in <ul> tags if any <li> exists
  if (formattedText.includes('<li>')) {
    formattedText = `<ul>${formattedText}</ul>`;
  }

  // Replace line breaks with <br> tags
  return formattedText.replace(/\n/g, '<br>');
}

// Toggle context visibility
function toggleContext(contextId) {
  const contextElement = document.getElementById(`context-${contextId}`);
  const toggleText = document.getElementById(`toggle-text-${contextId}`);
  if (!contextElement || !toggleText) return;

  const isExpanded = contextElement.style.display === 'block';
  contextElement.style.display = isExpanded ? 'none' : 'block';
  toggleText.textContent = isExpanded ? 'Show' : 'Hide';
  state.expandedContexts[contextId] = !isExpanded; // Persist state
}

// Escape HTML to prevent XSS
function escapeHtml(unsafe) {
  if (!unsafe) return '';
  unsafe = unsafe
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#039;')
  .replace(/%20/g, ' ');
  return unsafe;
}