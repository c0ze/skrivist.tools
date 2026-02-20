#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Skrivist UI Action - Adds "Send to Skriv" button to Calibre toolbar
"""

import os
import json
import uuid
from functools import partial

from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import error_dialog, info_dialog, question_dialog
from calibre.utils.config import JSONConfig

from qt.core import QMenu, QToolButton

# Plugin configuration stored in calibre config directory
prefs = JSONConfig('plugins/skrivist')
prefs.defaults['api_key'] = ''
prefs.defaults['server_url'] = 'https://api.skriv.ist'


class SkrivistAction(InterfaceAction):
    """
    Interface action that adds a toolbar button for sending books to Skrivist
    """
    name = 'Skrivist'
    action_spec = ('Send to Skriv', None, 'Send selected book(s) to your Skriv.ist library', 'Ctrl+Shift+K')
    popup_type = QToolButton.ToolButtonPopupMode.InstantPopup
    action_add_menu = True

    def genesis(self):
        """Setup the action and menu"""
        # Try custom icon, fall back to built-in cloud-upload icon
        try:
            icon = get_icons('images/icon.png', 'Skrivist')
        except Exception:
            from calibre.gui2 import get_icons as get_builtin_icons
            icon = get_builtin_icons('cloud-upload.png')

        self.qaction.setIcon(icon)
        self.qaction.triggered.connect(self.send_to_skriv)

        # Create menu
        self.menu = QMenu(self.gui)
        self.qaction.setMenu(self.menu)

        # Add menu items
        self.create_menu_actions()

    def create_menu_actions(self):
        """Create the dropdown menu actions"""
        self.menu.clear()

        # Send selected books
        send_action = self.menu.addAction('Send selected to Skriv')
        send_action.triggered.connect(self.send_to_skriv)

        self.menu.addSeparator()

        # Configure
        config_action = self.menu.addAction('Configure API Key...')
        config_action.triggered.connect(self.show_configuration)

    def send_to_skriv(self):
        """Send selected books to Skrivist cloud"""
        # Check API key is configured
        api_key = prefs['api_key']
        if not api_key:
            error_dialog(
                self.gui,
                'API Key Required',
                'Please configure your Skrivist API key first.',
                det_msg='Go to Preferences > Plugins > Skrivist to set your API key.',
                show=True
            )
            return

        # Get selected book IDs
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows:
            error_dialog(
                self.gui,
                'No Selection',
                'Please select one or more books to send.',
                show=True
            )
            return

        book_ids = list(map(self.gui.library_view.model().id, rows))

        # Confirm with user
        if len(book_ids) > 1:
            if not question_dialog(
                self.gui,
                'Confirm Upload',
                f'Send {len(book_ids)} books to Skriv.ist?'
            ):
                return

        # Send each book
        success_count = 0
        fail_count = 0

        for book_id in book_ids:
            try:
                self._upload_book(book_id, api_key)
                success_count += 1
            except Exception as e:
                fail_count += 1
                print(f'Failed to upload book {book_id}: {e}')

        # Show result
        if fail_count == 0:
            info_dialog(
                self.gui,
                'Upload Complete',
                f'Successfully sent {success_count} book(s) to Skriv.ist!',
                show=True
            )
        else:
            error_dialog(
                self.gui,
                'Upload Partially Failed',
                f'Sent {success_count} book(s), {fail_count} failed.',
                show=True
            )

    def _upload_book(self, book_id, api_key):
        """Upload a single book to Skrivist"""
        import urllib.request
        import urllib.error
        from calibre.ebooks.metadata.meta import get_metadata

        db = self.gui.current_db.new_api

        # Get book metadata
        mi = db.get_metadata(book_id, get_cover=True)

        # Get EPUB format (prefer EPUB, fall back to others)
        formats = db.formats(book_id)
        if not formats:
            raise ValueError('Book has no formats')

        # Prefer EPUB
        fmt = 'EPUB' if 'EPUB' in formats else formats[0]
        if fmt != 'EPUB':
            raise ValueError(f'Book is not in EPUB format (has: {formats})')

        # Get file path
        file_path = db.format_abspath(book_id, fmt)
        if not file_path or not os.path.exists(file_path):
            raise ValueError('Could not locate book file')

        # Prepare metadata
        metadata = {
            'title': mi.title or 'Unknown',
            'author': ', '.join(mi.authors) if mi.authors else 'Unknown',
            'language': mi.language if mi.language else 'en',
        }

        # Upload using multipart form data
        server_url = prefs['server_url'].rstrip('/')
        upload_url = f'{server_url}/v1/upload'

        # Build multipart request with random boundary
        boundary = f'----SkrivistBoundary{uuid.uuid4().hex}'

        body = []

        # Add metadata fields
        for key, value in metadata.items():
            body.append(f'--{boundary}'.encode())
            body.append(f'Content-Disposition: form-data; name="{key}"'.encode())
            body.append(b'')
            body.append(value.encode('utf-8'))

        # Add file
        with open(file_path, 'rb') as f:
            file_data = f.read()

        body.append(f'--{boundary}'.encode())
        body.append(f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(file_path)}"'.encode())
        body.append(b'Content-Type: application/epub+zip')
        body.append(b'')
        body.append(file_data)

        body.append(f'--{boundary}--'.encode())

        body_bytes = b'\r\n'.join(body)

        # Create request
        req = urllib.request.Request(upload_url, data=body_bytes)
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
        req.add_header('X-API-Key', api_key)

        # Send request
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                if not result.get('success'):
                    raise ValueError(result.get('error', 'Upload failed'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8', errors='replace')
            raise ValueError(f'Server error {e.code}: {error_body}')

    def show_configuration(self):
        """Show the configuration dialog"""
        self.interface_action_base_plugin.do_user_config(self.gui)
