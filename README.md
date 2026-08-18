# denote-spatial

Spatial canvas for [denote](https://github.com/protesilaos/denote) in Emacs.
It turns a denote directory into a draggable, resizeable
spatial canvas of images, pdfs, videos, and notes, opened in your browser.

The only external dependency is `python3`.


<img width="1912" height="943" alt="spatial" src="https://github.com/user-attachments/assets/f1a46d8d-e92e-4c20-807c-f9d1feda31b5" />




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
