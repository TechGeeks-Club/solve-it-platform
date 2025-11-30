// Challenge Details Page JavaScript

// Initialize CodeMirror
let editor;
let initialCode;
let canSubmit;

document.addEventListener("DOMContentLoaded", function () {
  // Get initial values from template (passed via data attributes or inline script)
  const editorElement = document.getElementById("codeEditor");
  if (!editorElement) return;

  // Get canSubmit from window object (set by inline script in template)
  canSubmit = window.canSubmit !== undefined ? window.canSubmit : true;
  initialCode = window.initialCode || editorElement.value;

  editor = CodeMirror.fromTextArea(editorElement, {
    lineNumbers: true,
    mode: "text/x-csrc",
    theme: "material-darker",
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

// Resizable panels functionality
document.addEventListener("DOMContentLoaded", function () {
  // Vertical resize (between problem and editor panels)
  const resizeHandle1 = document.getElementById("resizeHandle1");
  const problemPanel = document.getElementById("problemPanel");
  const editorPanel = document.getElementById("editorPanel");
  
  if (resizeHandle1 && problemPanel && editorPanel) {
    let isResizing = false;
    let startX = 0;
    let startWidth = 0;
    
    resizeHandle1.addEventListener("mousedown", function(e) {
      isResizing = true;
      startX = e.clientX;
      startWidth = problemPanel.offsetWidth;
      resizeHandle1.classList.add("resizing");
      document.body.classList.add("resizing");
      e.preventDefault();
    });
    
    document.addEventListener("mousemove", function(e) {
      if (!isResizing) return;
      
      const delta = e.clientX - startX;
      const newWidth = startWidth + delta;
      const containerWidth = problemPanel.parentElement.offsetWidth;
      const minWidth = 300; // Minimum width in pixels
      const handleWidth = 5; // Width of resize handle
      const maxWidth = containerWidth - 300 - handleWidth; // Leave space for editor and handle
      
      if (newWidth >= minWidth && newWidth <= maxWidth) {
        problemPanel.style.width = newWidth + "px";
        // Trigger CodeMirror refresh during resize for smooth rendering
        if (editor) {
          editor.refresh();
        }
      }
    });
    
    document.addEventListener("mouseup", function() {
      if (isResizing) {
        isResizing = false;
        resizeHandle1.classList.remove("resizing");
        document.body.classList.remove("resizing");
        
        // Refresh CodeMirror after resize
        if (editor) {
          setTimeout(() => editor.refresh(), 10);
        }
      }
    });
  }
  
  // Horizontal resize (between editor and test results)
  const resizeHandle2 = document.getElementById("resizeHandle2");
  const editorBody = document.getElementById("editorBody");
  const testResultsSection = document.getElementById("testResultsSection");
  
  if (resizeHandle2 && editorBody && testResultsSection) {
    let isResizingH = false;
    let startY = 0;
    let startHeight = 0;
    
    resizeHandle2.addEventListener("mousedown", function(e) {
      isResizingH = true;
      startY = e.clientY;
      startHeight = testResultsSection.offsetHeight;
      resizeHandle2.classList.add("resizing");
      document.body.classList.add("resizing-horizontal");
      e.preventDefault();
    });
    
    document.addEventListener("mousemove", function(e) {
      if (!isResizingH) return;
      
      const delta = startY - e.clientY; // Inverted because we're resizing from bottom
      const newHeight = startHeight + delta;
      const minHeight = 100; // Minimum height for test results
      const maxHeight = 600; // Maximum height for test results
      
      if (newHeight >= minHeight && newHeight <= maxHeight) {
        testResultsSection.style.height = newHeight + "px";
        // Trigger CodeMirror refresh during resize for smooth rendering
        if (editor) {
          editor.refresh();
        }
      }
    });
    
    document.addEventListener("mouseup", function() {
      if (isResizingH) {
        isResizingH = false;
        resizeHandle2.classList.remove("resizing");
        document.body.classList.remove("resizing-horizontal");
        
        // Refresh CodeMirror after resize
        if (editor) {
          setTimeout(() => editor.refresh(), 10);
        }
      }
    });
  }
});
