# denote-spatial

Spatial canvas for [denote](https://github.com/protesilaos/denote) in Emacs.
It turns a denote directory into a draggable, resizeable
spatial canvas of images, pdfs, videos, and notes, opened in your browser.

The only external dependency is `python3`.

<img width="1387" height="834" alt="dnsc" src="https://github.com/user-attachments/assets/07a6ee76-bb83-4cb3-bde9-37ee7ec5a3a6" />




## Features
 
- Grid, feed, cluster, and keyword views
- Drag and resize cards, alone or as a group
- Cluster mode groups linked notes together
- Click a link to jump straight to that note
- Images, videos, and pdfs supported
- Search / regex filter
- Layout is saved locally, notes are never modified

## Setup

Copy `denote-spatial.el`, `server.py`, and `index.html` into one folder
(e.g. `~/.emacs.d/lisp/denote-spatial/`).

```elisp
(add-to-list 'load-path "/path/to/this/folder")
(require 'denote-spatial)
(setq denote-spatial-notes-directory "~/denote")
```

## Usage

```
M-x denote-spatial-open
M-x denote-spatial-stop
```
