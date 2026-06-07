import { preprocessMarkdown } from '../../markdown'

export function transformVditor文章预览Html(html: string): string {
  return html
}

export function preprocessVditor文章Markdown(markdown: string): string {
  return preprocessMarkdown(markdown)
}

export function parseVditor文章预览(element: HTMLElement) {
  element.querySelectorAll<HTMLElement>('.card-github.fetch-waiting').forEach((card) => {
    card.classList.remove('fetch-waiting')
  })
}
