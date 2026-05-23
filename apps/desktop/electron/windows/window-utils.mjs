function showAndFocusWindow(window) {
  if (window.isMinimized()) {
    window.restore()
  }

  window.show()
  window.focus()
  return window
}

export {
  showAndFocusWindow,
}
