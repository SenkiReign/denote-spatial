;;; denote-spatial.el --- A canvas for denote -*- lexical-binding: t; -*-

;; Author:  Senki R.
;; Keywords: emacs, denote, notes, multimedia, moodboard
;; Package-Requires: ((emacs "27.1"))
;; Version: 0.1.0

;;; Commentary:

;; denote-spatial.el turns a denote directory into a
;; draggable, resizeable spatial canvas of images, pdfs, videos, and notes opened in your browser.
;;
;; The only external dependency is `python3'.
;;
;; Setup:
;;   (add-to-list 'load-path "/path/to/this/folder")
;;   (require 'denote-spatial)
;;   (setq denote-spatial-notes-directory "~/denote")
;;;
;; Usage:
;;   M-x denote-spatial-open   ; starts the server (if needed) + opens browser
;;   M-x denote-spatial-stop   ; stops the server

;;; Code:

(defgroup denote-spatial nil
  "Local spatial canvas for denote notes, images, and videos."
  :group 'convenience
  :prefix "denote-spatial-")

(defcustom denote-spatial-notes-directory nil
  "Directory of denote notes/images/videos to browse spatially.
If nil, `denote-spatial-open' first tries `denote-directory' (if the
`denote' package is loaded and configured), then falls back to
prompting once and remembering it for the session."
  :type '(choice (const :tag "Use denote-directory / ask" nil) directory)
  :group 'denote-spatial)

(defcustom denote-spatial-port 8420
  "Local port the denote-spatial server listens on (localhost only)."
  :type 'integer
  :group 'denote-spatial)

(defcustom denote-spatial-python-executable "python3"
  "Python 3 executable used to run the local server."
  :type 'string
  :group 'denote-spatial)

(defvar denote-spatial--process nil
  "The running denote-spatial server process, if any.")

(defvar denote-spatial--dir
  (file-name-directory
   (or load-file-name
       (and byte-compile-current-file (bound-and-true-p byte-compile-current-file))
       (buffer-file-name)))
  "Directory where `denote-spatial.el' lives (captured at load time).")

(defun denote-spatial--package-directory ()
  "Directory this file (and its bundled server.py/index.html) lives in."
  (or denote-spatial--dir
      (file-name-directory (locate-library "denote-spatial"))))

(defun denote-spatial--server-script ()
  "Path to the bundled server.py."
  (expand-file-name "server.py" (denote-spatial--package-directory)))

;;;###autoload
(defun denote-spatial-open ()
  "Start the denote-spatial server if needed, then open it in your browser.
If it's already running, just reopens the browser tab."
  (interactive)
  (unless (executable-find denote-spatial-python-executable)
    (user-error "denote-spatial: `%s' not found — Python 3 is the only dependency"
                denote-spatial-python-executable))
  (unless (file-exists-p (denote-spatial--server-script))
    (user-error "denote-spatial: server.py not found next to denote-spatial.el"))
  (unless denote-spatial-notes-directory
    (setq denote-spatial-notes-directory
          (or (and (fboundp 'denote-directory) (denote-directory))
              (read-directory-name "Denote directory for denote-spatial: "))))
  (let ((url (format "http://localhost:%d" denote-spatial-port)))
    (if (and denote-spatial--process (process-live-p denote-spatial--process))
        (browse-url url)
      (let ((process-environment (cons "DENOTE_SPATIAL_NO_OPEN=1" process-environment)))
        (setq denote-spatial--process
              (start-process "denote-spatial" "*denote-spatial*"
                              denote-spatial-python-executable
                              (denote-spatial--server-script)
                              (expand-file-name denote-spatial-notes-directory)
                              (number-to-string denote-spatial-port))))
      (message "denote-spatial: starting…")
      ;; give the server a beat to bind the port before we open the browser
      (run-at-time 0.8 nil (lambda () (browse-url url))))))

;;;###autoload
(defun denote-spatial-stop ()
  "Stop the denote-spatial server."
  (interactive)
  (if (and denote-spatial--process (process-live-p denote-spatial--process))
      (progn (delete-process denote-spatial--process)
             (setq denote-spatial--process nil)
             (message "denote-spatial: stopped"))
    (message "denote-spatial: not running")))

(provide 'denote-spatial)
;;; denote-spatial.el ends here
