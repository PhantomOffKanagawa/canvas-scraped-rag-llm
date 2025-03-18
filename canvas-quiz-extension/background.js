// Background script for Canvas Quiz Helper

// Store for question data and active windows
const dataStore = {
  answers: {},
  activeWindows: {}
};

// Initialize when the extension is installed
chrome.runtime.onInstalled.addListener(() => {
  console.log('Canvas Quiz Helper extension installed');
  
  // Create context menu items for quick access
  chrome.contextMenus.create({
    id: "answerCurrentQuestion",
    title: "Get answer for this question",
    contexts: ["page"],
    documentUrlPatterns: ["*://*.instructure.com/courses/*/quizzes/*"]
  });
});

// Listen for messages from the popup or results page
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'extractCurrentQuestion') {
    getCurrentQuestion(sender.tab ? sender.tab.id : message.tabId, sendResponse);
    return true; // Keep connection open for async response
  } 
  else if (message.action === 'extractAllQuestions') {
    getAllQuestions(sender.tab ? sender.tab.id : message.tabId, sendResponse);
    return true; // Keep connection open for async response
  }
  else if (message.action === 'getAnswerData') {
    const data = dataStore.answers[message.id];
    if (data) {
      sendResponse({success: true, data: data});
    } else {
      sendResponse({success: false, error: 'Answer data not found'});
    }
  }
});

// Extract the current question from the page
function getCurrentQuestion(tabId, sendResponse) {
  chrome.scripting.executeScript({
    target: {tabId},
    function: extractAllQuestionsFromPage
  }).then(results => {
    const questions = results[0].result;
    if (questions && questions.length > 0) {
      // Process the first unanswered question only
      const question = questions.find(q => !q.answered);
      processQuestions([question], tabId, sendResponse);
    } else {
      const windowId = openResultsWindow('error', null, 'Error', 'No question found');
      if (sendResponse) sendResponse({success: false, error: 'No question found', windowId});
    }
  }).catch(error => {
    console.error('Error extracting question:', error);
    const windowId = openResultsWindow('error', null, 'Error', error.message);
    if (sendResponse) sendResponse({success: false, error: error.message, windowId});
  });
}

// Extract all questions from the page
function getAllQuestions(tabId, sendResponse) {
  chrome.scripting.executeScript({
    target: {tabId},
    function: extractAllQuestionsFromPage
  }).then(results => {
    const questions = results[0].result;
    if (questions && questions.length > 0) {
      processQuestions(questions, tabId, sendResponse);
    } else {
      const windowId = openResultsWindow('error', null, 'Error', 'No questions found');
      if (sendResponse) sendResponse({success: false, error: 'No questions found', windowId});
    }
  }).catch(error => {
    console.error('Error extracting questions:', error);
    const windowId = openResultsWindow('error', null, 'Error', error.message);
    if (sendResponse) sendResponse({success: false, error: error.message, windowId});
  });
}

// Process multiple questions
function processQuestions(questions, tabId, sendResponse) {
  chrome.storage.sync.get(['apiKey', 'mode'], function(result) {
    const mode = result.mode || 'api';
    
    if (mode === 'copy') {
      // Copy all questions to clipboard
      const formattedQuestions = questions.map(q => formatQuestion(q)).join('\n\n---\n\n');
      
      // Use chrome.scripting to execute clipboard code in the page context
      chrome.scripting.executeScript({
        target: {tabId},
        function: (text) => {
          const textarea = document.createElement('textarea');
          textarea.value = text;
          document.body.appendChild(textarea);
          textarea.select();
          document.execCommand('copy');
          document.body.removeChild(textarea);
        },
        args: [formattedQuestions]
      }).then(() => {
        const windowId = openResultsWindow('info', null, 'Questions copied', `All ${questions.length} questions have been copied to your clipboard. You can now paste them into ChatGPT or another AI tool.`);
        if (sendResponse) sendResponse({success: true, windowId});
      }).catch(error => {
        const windowId = openResultsWindow('error', null, 'Copy Error', error.message);
        if (sendResponse) sendResponse({success: false, error: error.message, windowId});
      });
    } else if (mode === 'local') {
      // Local mode: process questions without API
      
      // Create a unique ID for this batch request
      const batchId = Date.now().toString();

      // Open loading window
      const windowId = openResultsWindow('loading', batchId, null, `Processing ${questions.length} questions...`);
      
      if (sendResponse) sendResponse({success: true, windowId});
      
      // Process questions sequentially
      localProcessQuestionsSequentially(questions, batchId);
    } else {
      // Use OpenAI API
      if (!result.apiKey) {
        const windowId = openResultsWindow('error', null, 'API Key Missing', 'Please add your OpenAI API key in the extension settings.');
        if (sendResponse) sendResponse({success: false, error: 'API key not found', windowId});
        return;
      }
      
      // Create a unique ID for this batch request
      const batchId = Date.now().toString();
      
      // Open loading window
      const windowId = openResultsWindow('loading', batchId, null, `Processing ${questions.length} questions...`);
      
      if (sendResponse) sendResponse({success: true, windowId});
      
      // Process questions sequentially
      processQuestionsSequentially(questions, result.apiKey, batchId);
    }
  });
}

async function localProcessQuestionsSequentially(questions, batchId) {
  try {
    const results = [];

    for (let i = 0; i < questions.length; i++) {
      // Update progress
      updateResultsWindow(batchId, 'loading', null, `Processing question ${i+1} of ${questions.length}...`);
      
      try {
        const answer = await sendToLocal(questions[i], 'local');
        results.push({
          question: questions[i],
          answer: answer.response,
          context: answer.context
        });

        // Store all results
        dataStore.answers[batchId] = {
          questions: results
        };
        
        // Small delay to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 500));
      } catch (error) {
        console.error('Error processing question:', error);
        // Store the error as the answer
        results.push({
          question: questions[i],
          answer: `Error: ${error.message}`
        });
        
        // Continue with next question even if one fails
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }
    
    // Store all results
    dataStore.answers[batchId] = {
      questions: results
    };
    
    // Update the results window with all answers
    updateResultsWindow(batchId, 'answer', null, null);

    
  } catch (error) {
    updateResultsWindow(batchId, 'error', 'Error', 'Failed to process all questions: ' + error.message);
  }
}


// Send question to Local LLM API
async function sendToLocal(question, apiKey) {
  const formattedQuestion = formatQuestion(question);
  
  const response = await fetch('http://localhost:5000/ask', { // Updated URL for local LLM API
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      query: question.text,
      answers: question.answers,
    })
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error?.message || 'API request failed');
  }
  
  const data = await response.json();
  console.log('Local LLM response:', data);
  return {response: data.response,
          context: data.context};
}

// Process questions sequentially to avoid rate limiting
async function processQuestionsSequentially(questions, apiKey, batchId) {
  try {
    const results = [];
    
    for (let i = 0; i < questions.length; i++) {
      // Update progress
      updateResultsWindow(batchId, 'loading', null, `Processing question ${i+1} of ${questions.length}...`);
      
      try {
        const answer = await sendToOpenAI(questions[i], apiKey);
        results.push({
          question: questions[i],
          answer: answer
        });

        
        // Store all results
        dataStore.answers[batchId] = {
          questions: results
        };
        
        // Small delay to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 500));
      } catch (error) {
        console.error('Error processing question:', error);
        // Store the error as the answer
        results.push({
          question: questions[i],
          answer: `Error: ${error.message}`
        });
        
        // Continue with next question even if one fails
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }
    
    // Store all results
    dataStore.answers[batchId] = {
      questions: results
    };

    // Update the results window with all answers
    updateResultsWindow(batchId, 'answer', null, null);
    
  } catch (error) {
    updateResultsWindow(batchId, 'error', 'Error', 'Failed to process all questions: ' + error.message);
  }
}

// Format a question for clipboard copy or API
function formatQuestion(question) {
  let formatted = 'Question: ' + question.text;
  
  if (question.answers && question.answers.length > 0) {
    formatted += '\n\nAnswer choices:';
    question.answers.forEach((answer, index) => {
      formatted += '\n' + String.fromCharCode(65 + index) + ') ' + answer;
    });
  }
  
  return formatted;
}

// Send question to OpenAI API
async function sendToOpenAI(question, apiKey) {
  const formattedQuestion = formatQuestion(question);
  
  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      model: 'gpt-4o-mini',
      messages: [
        {
          role: 'system',
          content: 'You are a helpful AI tutor. Answer the following quiz question concisely but with complete explanation.'
        },
        {
          role: 'user',
          content: formattedQuestion
        }
      ],
      temperature: 0.7
    })
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error?.message || 'API request failed');
  }
  
  const data = await response.json();
  return data.choices[0].message.content;
}

// Open a new window with the results page
function openResultsWindow(action, id, title, message) {
  const url = new URL(chrome.runtime.getURL('results.html'));
  url.searchParams.append('action', action);
  if (id) url.searchParams.append('id', id);
  if (title) url.searchParams.append('title', encodeURIComponent(title));
  if (message) url.searchParams.append('message', encodeURIComponent(message));
  
  return chrome.windows.create({
    url: url.toString(),
    type: 'popup',
    width: 800,
    height: 600
  }).then(window => {
    if (id) {
      dataStore.activeWindows[id] = window.id;
    }
    return window.id;
  }).catch(error => {
    console.error('Error opening results window:', error);
    return null;
  });
}

// Update an existing results window
function updateResultsWindow(id, action, title, message) {
  if (!dataStore.activeWindows[id]) return;
  
  // Find all tabs in the target window
  chrome.tabs.query({ windowId: dataStore.activeWindows[id] }, function(tabs) {
    if (tabs.length > 0) {
      // Send message to the tab
      chrome.tabs.sendMessage(tabs[0].id, {
        action: action === 'loading' ? 'updateLoading' : 'show' + capitalize(action),
        id: id,
        title: title,
        message: message,
        data: dataStore.answers[id]
      });
    }
  });
}

// Helper function to capitalize first letter
function capitalize(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

function extractAllQuestionsFromPage() {
  const questionHolders = document.querySelectorAll('.question_holder:has(.question:not(.answered))');
  // Filter out answered questions
  if (!questionHolders.length) {
    return [];
  }

  const questions = [];
  questionHolders.forEach(holder => {
    try {
      const question = extractQuestionData(holder);
      if (question) {
        questions.push(question);
      }
    } catch (error) {
      console.error('Error extracting question:', error);
    }
  });

  return questions;
  
  function extractQuestionData(questionHolder) {
    const questionElement = questionHolder.querySelector('.question');
    if (!questionElement) return null;

    const answered = questionHolder.classList.contains('answered')
  
    // Extract question text
    const questionTextElement = questionElement.querySelector('.question_text');
    if (!questionTextElement) return null;
    const questionText = questionTextElement.textContent.trim();
  
    // Extract answer choices if present
    const answerElements = questionElement.querySelectorAll('.answer');
    const answers = [];
  
    answerElements.forEach(answerElement => {
      const answerLabel = answerElement.querySelector('.answer_label');
      const backupAnswerLabel = answerElement.querySelector('.select_answer > label');
      if (answerLabel) {
        answers.push(answerLabel.textContent.trim());
      } else if (backupAnswerLabel) {
        answers.push(backupAnswerLabel.textContent.trim());
      }
    });
  
    // Extract question number/name if present
    const questionName = questionHolder.querySelector('.question_name');
    const questionNumber = questionName ? questionName.textContent.trim() : 'Question';
  
    return {
      text: questionText,
      answers: answers,
      number: questionNumber,
      answered: answered
    };
  }
}