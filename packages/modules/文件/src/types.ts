export type FilePurpose = 'file' | 'article_image' | 'moment_image' | 'media_asset'

export interface FileItem {
  id: string
  folder_id: string | null
  purpose: FilePurpose
  original_name: string
  url: string
  thumbnail_url: string | null
  size: number
  mime_type: string
  created_at: string
  article_id: string | null
  article_title: string | null
  moment_id: string | null
  moment_title: string | null
  media_item_id: string | null
  media_title: string | null
  media_asset_type: string | null
}

export interface FileFolderItem {
  id: string
  parent_id: string | null
  name: string
  created_at: string
  updated_at: string
}

export interface FileTreeNode {
  id: string
  parent_id: string | null
  name: string
  children: FileTreeNode[]
}

export interface FileBreadcrumbItem {
  id: string | null
  name: string
}

export interface FileExplorerData {
  current_folder: FileFolderItem | null
  breadcrumbs: FileBreadcrumbItem[]
  tree: FileTreeNode[]
  folders: FileFolderItem[]
  files: FileItem[]
}

export interface FileSearchFolderItem {
  id: string
  parent_id: string | null
  name: string
  path: string
  updated_at: string
}

export interface FileSearchFileItem {
  id: string
  folder_id: string | null
  purpose: FilePurpose
  original_name: string
  url: string
  thumbnail_url: string | null
  size: number
  mime_type: string
  created_at: string
  path: string
  article_id: string | null
  article_title: string | null
  moment_id: string | null
  moment_title: string | null
  media_item_id: string | null
  media_title: string | null
  media_asset_type: string | null
}

export interface FileSearchData {
  folders: FileSearchFolderItem[]
  files: FileSearchFileItem[]
}
