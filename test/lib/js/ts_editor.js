document.addEventListener("DOMContentLoaded", function() {
    CodeMirror.fromTextArea(document.getElementById("codeEditor"), {
      lineNumbers: true,       // Display line numbers
      mode: "text/x-csrc",     // Mode for C language
      theme: "monokai",        // Theme
      indentUnit: 4,           // Number of spaces for indentation
      matchBrackets: true      // Highlight matching brackets
    });
  });