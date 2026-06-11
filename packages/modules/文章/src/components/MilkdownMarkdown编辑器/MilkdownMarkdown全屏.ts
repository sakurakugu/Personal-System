import { nextTick, type Ref } from 'vue'

export function getMilkdownMarkdownFullscreenRoot(
  rootRef: Ref<HTMLElement | null>,
  fullscreenRootSelector: string,
): HTMLElement | null {
  const root = rootRef.value?.closest('.milkdown-markdown-editor')
  if (!(root instanceof HTMLElement)) {
    return null
  }

  if (!fullscreenRootSelector) {
    return root
  }

  const fullscreenRoot = root.closest(fullscreenRootSelector)
  return fullscreenRoot instanceof HTMLElement ? fullscreenRoot : root
}

export function toggleMilkdownMarkdownPageFullscreen(root: HTMLElement | null) {
  if (!(root instanceof HTMLElement)) {
    return
  }

  root.classList.toggle('milkdown-markdown-editor--page-fullscreen')
  void nextTick(() => {
    root.scrollIntoView({ block: 'nearest' })
    window.dispatchEvent(new Event('resize'))
  })
}

export async function toggleMilkdownMarkdownScreenFullscreen(root: HTMLElement | null) {
  if (!(root instanceof HTMLElement) || !document.fullscreenEnabled) {
    toggleMilkdownMarkdownPageFullscreen(root)
    return
  }

  if (document.fullscreenElement) {
    await document.exitFullscreen()
    return
  }

  await root.requestFullscreen()
}
