// Challenge Details Page JavaScript

// Initialize CodeMirror
let editor;
let initialCode;
let canSubmit;

document.addEventListener("DOMContentLoaded", function () {
  // Get initial values from template (passed via data attributes or inline script)
  const editorElement = document.getElementById("codeEditor");
  if (!editorElement) return;

  editor = CodeMirror.fromTextArea(editorElement, {
    lineNumbers: true,
    mode: "text/x-csrc",
    theme: "monokai",
    indentUnit: 4,
    tabSize: 4,
    matchBrackets: true,
    autoCloseBrackets: true,
    readOnly: !canSubmit,
    lineWrapping: false,
    extraKeys: {
      "Tab": function(cm) {
        if (cm.somethingSelected()) {
          cm.indentSelection("add");
        } else {
          cm.replaceSelection("    ", "end");
        }
      }
    }
  });

  editor.setSize(null, "100%");
});

// Reset button
function resetCode() {
  const resetBtn = document.getElementById("resetBtn");
  if (resetBtn && !resetBtn.disabled && editor) {
    editor.setValue(initialCode);
  }
}

document.getElementById("resetBtn")?.addEventListener("click", resetCode);

// Submit button
function submitCode() {
  const submitBtn = document.getElementById("submitBtn");
  if (!submitBtn || submitBtn.disabled) return;
  
  const code = editor ? editor.getValue() : document.getElementById("codeEditor").value;

  if (!code.trim()) {
    alert("Please write some code before submitting!");
    return;
  }

  // Check if there's a previous submission
  const hasPreviousSubmission = submitBtn.dataset.hasPrevious === 'true';
  const currentAttempts = parseInt(submitBtn.dataset.currentAttempts || '0');
  const currentScore = parseInt(submitBtn.dataset.currentScore || '0');
  const maxAttempts = parseInt(submitBtn.dataset.maxAttempts || '0');
  
  if (hasPreviousSubmission && currentAttempts > 0) {
    const confirmed = confirm(
      "⚠️ Warning: This submission will overwrite your previous attempt.\n\n" +
      "Your current score: " + currentScore + "%\n" +
      "Attempts used: " + currentAttempts + "/" + maxAttempts + "\n\n" +
      "Are you sure you want to continue?"
    );
    
    if (!confirmed) {
      return; // User cancelled, don't submit
    }
  }

  // Disable button immediately and show loading state
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<div class="spinner"></div> Submitting...';
  submitBtn.className = 'btn btn-warning';

  const file = new Blob([code], { type: "text/plain" });
  const inputElement = document.getElementById("uploadedFile");
  const dataTransfer = new DataTransfer();
  dataTransfer.items.add(new File([file], "code.c"));
  inputElement.files = dataTransfer.files;

  document.getElementById("hiddenForm").submit();
}

document.getElementById("submitBtn")?.addEventListener("click", submitCode);

// Toggle test case accordion
function toggleTestCase(index) {
  const details = document.getElementById(`test-details-${index}`);
  const icon = document.getElementById(`accordion-icon-${index}`);
  
  if (details && icon) {
    if (details.classList.contains('expanded')) {
      details.classList.remove('expanded');
      icon.classList.remove('expanded');
    } else {
      details.classList.add('expanded');
      icon.classList.add('expanded');
    }
  }
}

// Make function globally available for onclick handlers
window.toggleTestCase = toggleTestCase;
