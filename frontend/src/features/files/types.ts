export interface FileItem {
  id: string
  folder_id: string | null
  original_name: string
  url: string
  size: number
  mime_type: string
  created_at: string
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
  original_name: string
  url: string
  size: number
  mime_type: string
  created_at: string
  path: string
}

export interface FileSearchData {
  folders: FileSearchFolderItem[]
  files: FileSearchFileItem[]
}
