---
title: Vim and Neovim Config
date: 2026-11-23
language: Lua
---

```{file="_vimrc"}
" =============================================================================
" GENERAL SETTINGS
" =============================================================================
set nocompatible
syntax on
filetype on
set termguicolors
colorscheme slate

set encoding=UTF-8
set fileencoding=utf-8
set updatetime=250
set timeoutlen=400

set undofile
set undodir=~/.vim/undodir

set number
set relativenumber
set numberwidth=4
set signcolumn=yes

set nocursorline
set scrolloff=8
set sidescrolloff=8
set wrap nowrap
set breakindent
set whichwrap+=<,>,[,],h,l

set mouse=a
set belloff=all
set showmatch
set showcmd
set showmode
set cmdheight=1
set showtabline=2
set laststatus=2
set shortmess+=c

set statusline=%f%=%l/%L

set incsearch
set hlsearch
set ignorecase
set smartcase

set wildmenu
set wildmode=longest:full,full
set wildignorecase
set wildignore=*.docx,*.jpg,*.png,*.gif,*.pdf,*.pyc,*.exe,*.flv,*.img,*.xlsx
set completeopt=menuone,noselect
set pumheight=10

set autoindent
set smartindent
set tabstop=4
set softtabstop=4
set shiftwidth=4

set backspace=indent,eol,start
set iskeyword+=-

set nobackup
set nowritebackup
set noswapfile
set confirm
set path+=**

set splitbelow
set splitright

" Netrw (File Explorer)
let g:netrw_banner=0
let g:netrw_liststyle=3
let g:netrw_showhide=1
let g:netrw_winsize=20
let g:netrw_fastbrowse = 0
let g:netrw_keepdir = 0

" =============================================================================
" KEYMAPS
" =============================================================================
let mapleader = " "
let maplocalleader = " "

" General Shortcuts
nnoremap <Space> <Nop>
vnoremap <Space> <Nop>
noremap ; :
nnoremap <Esc> :noh<CR>

nnoremap <C-s> :w<CR>
nnoremap <leader>s :w<CR>
nnoremap <C-q> :q<CR>
nnoremap <leader>a ggVG

" Navigation & Movement
nnoremap <expr> k v:count == 0 ? 'gk' : 'k'
nnoremap <expr> j v:count == 0 ? 'gj' : 'j'
noremap <C-k> {
noremap <C-j> }
nnoremap <C-d> <C-d>zz        " Scroll and center
nnoremap <C-u> <C-u>zz
nnoremap n nzzzv              " Search and center
nnoremap N Nzzzv

nnoremap <leader>v <C-w>v     " Vertical split
nnoremap <leader>h <C-w>s     " Horizontal split
nnoremap <leader>se <C-w>=    " Equalize splits
nnoremap <leader>q :close<CR> " Close current split

nnoremap <A-k> :wincmd k<CR>
nnoremap <A-j> :wincmd j<CR>
nnoremap <A-h> :wincmd h<CR>
nnoremap <A-l> :wincmd l<CR>

nnoremap <Up> :resize -2<CR>
nnoremap <Down> :resize +2<CR>
nnoremap <Left> :vertical resize -2<CR>
nnoremap <Right> :vertical resize +2<CR>

nnoremap <leader>n :tabnew<CR>
nnoremap <leader>x :tabclose<CR>
nnoremap <TAB> :tabn<CR>
nnoremap <S-TAB> :tabp<CR>

nnoremap x "_x
nnoremap <leader>+ <C-a>
nnoremap <leader>- <C-x>
nnoremap <leader>lw :set wrap!<CR>

" Mode Tweaks
vnoremap < <gv
vnoremap > >gv
vnoremap p "_dP
vnoremap fj <ESC>
vnoremap jf <ESC>

inoremap /* /**/<left><left>
inoremap fj <ESC>
inoremap jf <ESC>

" Clipboard
noremap <leader>y "+y
noremap <leader>p "+p
noremap <leader>P "+P

" File Explorer & Terminal
noremap <silent> <leader>e :Lex<CR>
noremap <leader>o :Explore<CR>
noremap <a-`> :ter<CR>
tnoremap <a-`> exit<CR>
tnoremap <c-i> <c-w><s-n>
tnoremap <Esc> <C-\><C-n>

" Quick file find
nnoremap <leader>ff :find *
nnoremap <leader>fs :sfind *
nnoremap <leader>fv :vert sfind *
```

```{.lua file="init.lua"}
-- =============================================================================
-- GENERAL SETTINGS
-- =============================================================================

vim.opt.encoding = "utf-8"
vim.opt.fileencoding = "utf-8"

vim.cmd("syntax on")
vim.cmd("filetype on")
vim.opt.termguicolors = true
vim.cmd("colorscheme slate")

vim.opt.updatetime = 250
vim.opt.timeoutlen = 400

vim.opt.undofile = true
vim.opt.undodir = vim.fn.expand("~/.vim/undodir")
vim.fn.mkdir(vim.fn.expand("~/.vim/undodir"), "p")

vim.opt.number = true
vim.opt.relativenumber = true
vim.opt.numberwidth = 4
vim.opt.signcolumn = "yes"

vim.opt.cursorline = false
vim.opt.scrolloff = 8
vim.opt.sidescrolloff = 8
vim.opt.wrap = false
vim.opt.breakindent = true
vim.opt.whichwrap:append("<,>,[,],h,l")

vim.opt.mouse = "a"
vim.opt.belloff = "all"
vim.opt.showmatch = true
vim.opt.showcmd = true
vim.opt.showmode = true
vim.opt.cmdheight = 1
vim.opt.showtabline = 2
vim.opt.laststatus = 2
vim.opt.shortmess:append("c")

vim.opt.statusline = "%f%=%l/%L"

vim.opt.incsearch = true
vim.opt.hlsearch = true
vim.opt.ignorecase = true
vim.opt.smartcase = true

vim.opt.wildmenu = true
vim.opt.wildmode = { "longest:full", "full" }
vim.opt.wildignorecase = true
vim.opt.wildignore = {
  "*.docx",
  "*.jpg",
  "*.png",
  "*.gif",
  "*.pdf",
  "*.pyc",
  "*.exe",
  "*.flv",
  "*.img",
  "*.xlsx",
}
vim.opt.completeopt = { "menuone", "noselect" }
vim.opt.pumheight = 10

vim.opt.autoindent = true
vim.opt.smartindent = true
vim.opt.tabstop = 4
vim.opt.softtabstop = 4
vim.opt.shiftwidth = 4
vim.opt.backspace = { "indent", "eol", "start" }
vim.opt.iskeyword:append("-")

vim.opt.backup = false
vim.opt.writebackup = false
vim.opt.swapfile = false
vim.opt.confirm = true
vim.opt.path:append("**")

vim.opt.splitbelow = true
vim.opt.splitright = true


-- Newtr (File Explorer)
vim.g.netrw_banner = 0
vim.g.netrw_liststyle = 3
vim.g.netrw_showhide = 1
vim.g.netrw_winsize = 20
vim.g.netrw_fastbrowse = 0
vim.g.netrw_keepdir = 0


-- =============================================================================
-- KEYMAPS
-- =============================================================================

vim.g.mapleader = " "
vim.g.maplocalleader = " "

local map = vim.keymap.set

-- General shortcuts
map({ "n", "v" }, "<Space>", "<Nop>")
map({ "n", "v" }, ";", ":")

map("n", "<Esc>", "<cmd>nohlsearch<CR>")

map("n", "<C-s>", "<cmd>write<CR>")
map("n", "<leader>s", "<cmd>write<CR>")
map("n", "<C-q>", "<cmd>quit<CR>")
map("n", "<leader>a", "ggVG")

-- Navigation and movement
map("n", "k", function()
  return vim.v.count == 0 and "gk" or "k"
end, { expr = true })

map("n", "j", function()
  return vim.v.count == 0 and "gj" or "j"
end, { expr = true })

map({ "n", "v", "o" }, "<C-k>", "{")
map({ "n", "v", "o" }, "<C-j>", "}")

map("n", "<C-d>", "<C-d>zz")
map("n", "<C-u>", "<C-u>zz")

map("n", "n", "nzzzv")
map("n", "N", "Nzzzv")

map("n", "<leader>v", "<C-w>v")
map("n", "<leader>h", "<C-w>s")
map("n", "<leader>se", "<C-w>=")
map("n", "<leader>q", "<cmd>close<CR>")

map("n", "<A-k>", "<cmd>wincmd k<CR>")
map("n", "<A-j>", "<cmd>wincmd j<CR>")
map("n", "<A-h>", "<cmd>wincmd h<CR>")
map("n", "<A-l>", "<cmd>wincmd l<CR>")

map("n", "<Up>", "<cmd>resize -2<CR>")
map("n", "<Down>", "<cmd>resize +2<CR>")
map("n", "<Left>", "<cmd>vertical resize -2<CR>")
map("n", "<Right>", "<cmd>vertical resize +2<CR>")

map("n", "<leader>n", "<cmd>tabnew<CR>")
map("n", "<leader>x", "<cmd>tabclose<CR>")
map("n", "<Tab>", "<cmd>tabnext<CR>")
map("n", "<S-Tab>", "<cmd>tabprevious<CR>")

map("n", "x", '"_x')
map("n", "<leader>+", "<C-a>")
map("n", "<leader>-", "<C-x>")
map("n", "<leader>lw", "<cmd>set wrap!<CR>")

map("v", "<", "<gv")
map("v", ">", ">gv")
map("v", "p", '"_dP')
map("v", "fj", "<Esc>")
map("v", "jf", "<Esc>")

-- Mode tweaks
map("i", "/*", "/**/<Left><Left>")
map("i", "fj", "<Esc>")
map("i", "jf", "<Esc>")

map({ "n", "v" }, "<leader>y", '"+y')
map({ "n", "v" }, "<leader>p", '"+p')
map({ "n", "v" }, "<leader>P", '"+P')

map("n", "<leader>e", "<cmd>Lex<CR>", { silent = true })
map("n", "<leader>o", "<cmd>Explore<CR>")
map("n", "<A-`>", "<cmd>terminal<CR>")

map("t", "<A-`>", "exit<CR>")
map("t", "<C-i>", "<C-w><S-n>")
map("t", "<Esc>", "<C-\\><C-n>")

-- Quick file finding
map("n", "<leader>ff", ":find *")
map("n", "<leader>fs", ":sfind *")
map("n", "<leader>fv", ":vert sfind *")
```
