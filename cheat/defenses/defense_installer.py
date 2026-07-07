import os
import shutil
import stat


HTML_INSERT_TYPES = {
    "html_response_comment",
    "template_file",
    "static_html_file",
    "php_mixed_html",
    "sinatra_erb_template",
}

INLINE_HTML_TYPES = {
    "python_inline_html",
    "php_echo_html",
    "node_inline_html",
    "ruby_inline_erb",
}

class DefenseInstaller:
    def __init__(self, logger):
        self.logger = logger

    def check_permissions(self, asset_path):
        """
        Checks if the program has sufficient permissions to:
        1. Move the binary to _original.
        2. Write a new binary in its place.
        3. Set ownership of the new binary to match the original binary.
        4. Set permissions of the new binary to match the original binary.
        This is done by enumerating the file's metadata and current process capabilities.
        """
        try:
            # Get the current permissions and ownership of the asset
            asset_stat = os.stat(asset_path)
            asset_uid = asset_stat.st_uid
            asset_gid = asset_stat.st_gid
            asset_mode = stat.S_IMODE(asset_stat.st_mode)

            # Check if we can rename the binary
            # To rename, we need write and execute permissions on the containing directory
            asset_dir = os.path.dirname(asset_path)
            if not os.access(asset_dir, os.W_OK | os.X_OK):
                raise PermissionError(f"Cannot rename binary: insufficient permissions on directory {asset_dir}.")

            # Check if we can write a new binary in its place
            # Requires write permissions on the directory
            if not os.access(asset_dir, os.W_OK):
                raise PermissionError(f"Cannot write a new binary: insufficient permissions on directory {asset_dir}.")

            # Check if we can set ownership to match the original binary
            # Requires root privileges if we are not the owner of the file
            if os.geteuid() != 0 and (os.geteuid() != asset_uid or os.getegid() != asset_gid):
                raise PermissionError(
                    f"Cannot set ownership: process must run as root or match the file owner (UID: {asset_uid})."
                )

            # Check if we can set permissions to match the original binary
            # Requires write permissions on the file or directory
            if not os.access(asset_path, os.W_OK):
                raise PermissionError(f"Cannot set permissions: insufficient write permissions on {asset_path}.")

            self.logger.info(
                f"Permissions check passed for {asset_path}. "
                f"Mode: {oct(asset_mode)}, UID: {asset_uid}, GID: {asset_gid}"
            )
            return True
        except PermissionError as pe:
            self.logger.error(f"Permission error: {str(pe)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during permission check: {str(e)}")
            return False

    def install_defense(self, asset_type, asset_path, defense_obj):
        """
        Installs the defense by adding the prefix and suffix to the asset.
        """
        try:
            # Check permissions before proceeding
            if not self.check_permissions(asset_path):
                self.logger.error(f"Insufficient permissions for installing defense on: {asset_path}")
                return False
        
            prefix = defense_obj.get("prefix", "")
            suffix = defense_obj.get("suffix", "")

            if asset_type == "local_file":
                self._write_prefix_suffix_to_file(asset_path, prefix, suffix)
            elif asset_type == "web_file":
                self._write_prefix_suffix_to_file(asset_path, prefix, suffix)
            elif asset_type in HTML_INSERT_TYPES:
                self._insert_html_comment(asset_path, prefix, suffix)
            elif asset_type in INLINE_HTML_TYPES:
                self._insert_inline_html_comment(asset_path, prefix, suffix)
            elif asset_type == "flask_response_hook":
                self._install_flask_response_hook(asset_path, prefix, suffix)
            elif asset_type == "express_response_hook":
                self._install_express_response_hook(asset_path, prefix, suffix)
            elif asset_type == "sinatra_response_hook":
                self._install_sinatra_response_hook(asset_path, prefix, suffix)
            elif asset_type == "tool_wrapper":
                self._create_tool_wrapper_with_prefix_suffix(asset_path, prefix, suffix)
            else:
                raise ValueError(f"Unknown asset type: {asset_type}")

            self.logger.info(f"Defense successfully installed on {asset_path} of type {asset_type}.")
            return True
        except Exception as e:
            self.logger.info(f"Failed to install defense: {str(e)}")
            return False

    def remove_defense(self, asset_type, asset_path, defense_obj):
        """
        Removes a previously installed defense based on asset type and path.
        """
        try:
            # Check permissions before proceeding
            if not self.check_permissions(asset_path):
                self.logger.error(f"Insufficient permissions for installing defense on: {asset_path}")
                return False
        
            prefix = defense_obj.get("prefix", "")
            suffix = defense_obj.get("suffix", "")

            if (
                asset_type == "local_file"
                or asset_type == "web_file"
                or asset_type in HTML_INSERT_TYPES
                or asset_type in INLINE_HTML_TYPES
            ):
                self._remove_prefix_suffix_from_file(asset_path, prefix, suffix)
            elif asset_type == "tool_wrapper":
                self._restore_tool(asset_path)
            else:
                raise ValueError(f"Unknown asset type: {asset_type}")

            self.logger.info(f"Defense successfully removed from {asset_path} of type {asset_type}.")
            return True
        except Exception as e:
            self.logger.info(f"Failed to remove defense: {str(e)}")
            return False

    def _write_prefix_suffix_to_file(self, file_path, prefix, suffix):
        """
        Adds the prefix at the beginning and the suffix at the end of a file.
        """
        try:
            with open(file_path, 'r') as file:
                content = file.read()

            content = f"{prefix}{content}{suffix}"

            with open(file_path, 'w') as file:
                file.write(content)

            self.logger.info(f"Prefix and suffix added to file: {file_path}")
        except Exception as e:
            self.logger.info(f"Failed to write prefix and suffix to file: {str(e)}")

    def _combined_comment(self, prefix, suffix):
        return f"{prefix.rstrip()}\n{suffix.lstrip()}"

    def _insert_before_body_or_append(self, content, insertion):
        marker = "</body>"
        lower = content.lower()
        index = lower.rfind(marker)
        if index >= 0:
            return f"{content[:index]}{insertion}\n{content[index:]}"
        return f"{content.rstrip()}\n{insertion}\n"

    def _insert_html_comment(self, file_path, prefix, suffix):
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as file:
                content = file.read()
            insertion = self._combined_comment(prefix, suffix)
            updated = self._insert_before_body_or_append(content, insertion)
            if updated == content:
                raise ValueError("HTML comment insertion did not change content")
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(updated)
            self.logger.info(f"HTML response comment inserted into file: {file_path}")
        except Exception as e:
            self.logger.info(f"Failed to insert HTML response comment: {str(e)}")
            raise

    def _insert_inline_html_comment(self, file_path, prefix, suffix):
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as file:
                content = file.read()
            if "</body>" not in content.lower():
                raise ValueError("inline HTML body marker not found")
            insertion = self._combined_comment(prefix, suffix)
            updated = self._insert_before_body_or_append(content, insertion)
            if updated == content:
                raise ValueError("inline HTML insertion did not change content")
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(updated)
            self.logger.info(f"Inline HTML response comment inserted into file: {file_path}")
        except Exception as e:
            self.logger.info(f"Failed to insert inline HTML response comment: {str(e)}")
            raise

    def _insert_before_python_main_guard(self, content, insertion):
        marker = "\nif __name__"
        index = content.find(marker)
        if index >= 0:
            return f"{content[:index]}\n{insertion}\n{content[index:]}"
        return f"{content.rstrip()}\n\n{insertion}\n"

    def _install_flask_response_hook(self, file_path, prefix, suffix):
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as file:
                content = file.read()
            if "_cheat_after_request" in content:
                return
            comment = self._combined_comment(prefix, suffix)
            hook = f'''
_CHEAT_HTML_COMMENT = {comment!r}

try:
    @app.after_request
    def _cheat_after_request(response):
        content_type = response.headers.get("Content-Type", "")
        if getattr(response, "direct_passthrough", False):
            return response
        body = response.get_data(as_text=True)
        looks_html = "text/html" in content_type.lower() or "<html" in body.lower() or "</body>" in body.lower()
        if looks_html and _CHEAT_HTML_COMMENT not in body:
            response.set_data(body + "\\n" + _CHEAT_HTML_COMMENT + "\\n")
            response.headers.pop("Content-Length", None)
        return response
except NameError:
    pass
'''.strip()
            updated = self._insert_before_python_main_guard(content, hook)
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(updated)
            self.logger.info(f"Flask response hook inserted into file: {file_path}")
        except Exception as e:
            self.logger.info(f"Failed to insert Flask response hook: {str(e)}")
            raise

    def _install_express_response_hook(self, file_path, prefix, suffix):
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as file:
                content = file.read()
            if "__cheatHtmlComment" in content:
                return
            comment = self._combined_comment(prefix, suffix)
            hook = f"""
const __cheatHtmlComment = {comment!r};
app.use((req, res, next) => {{
  const __cheatSend = res.send.bind(res);
  res.send = function (body) {{
    const type = String(res.getHeader('Content-Type') || '').toLowerCase();
    const text = typeof body === 'string' ? body : Buffer.isBuffer(body) ? body.toString('utf8') : '';
    const looksHtml = type.includes('text/html') || text.toLowerCase().includes('<html') || text.toLowerCase().includes('</body>');
    if (typeof body === 'string' && looksHtml && !body.includes(__cheatHtmlComment)) {{
      body = body + '\\n' + __cheatHtmlComment + '\\n';
      res.removeHeader('Content-Length');
    }}
    return __cheatSend(body);
  }};
  next();
}});
""".strip()
            marker = "express()"
            index = content.find(marker)
            if index < 0:
                raise ValueError("express() marker not found")
            line_end = content.find("\n", index)
            if line_end < 0:
                line_end = len(content)
            updated = f"{content[:line_end + 1]}\n{hook}\n{content[line_end + 1:]}"
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(updated)
            self.logger.info(f"Express response hook inserted into file: {file_path}")
        except Exception as e:
            self.logger.info(f"Failed to insert Express response hook: {str(e)}")
            raise

    def _install_sinatra_response_hook(self, file_path, prefix, suffix):
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as file:
                content = file.read()
            if "_CHEAT_HTML_COMMENT" in content:
                return
            comment = self._combined_comment(prefix, suffix)
            hook = f'''
_CHEAT_HTML_COMMENT = {comment!r}

after do
  content_type = response['Content-Type'].to_s.downcase
  joined_body = body.respond_to?(:each) ? body.each.to_a.join : body.to_s
  if (content_type.include?('text/html') || joined_body.downcase.include?('<html') || joined_body.downcase.include?('</body>')) && !joined_body.include?(_CHEAT_HTML_COMMENT)
    body joined_body + "\\n" + _CHEAT_HTML_COMMENT + "\\n"
  end
end
'''.strip()
            updated = f"{hook}\n\n{content}"
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(updated)
            self.logger.info(f"Sinatra response hook inserted into file: {file_path}")
        except Exception as e:
            self.logger.info(f"Failed to insert Sinatra response hook: {str(e)}")
            raise

    def _create_tool_wrapper_with_prefix_suffix(self, tool_path, prefix, suffix):
        """
        Creates a wrapper script for a tool to inject a prefix and suffix defense,
        preserving the original permissions and ownership, and ensuring the original binary
        is kept in the same directory as the wrapper.
        """
        try:
            # Generate the path for the original binary
            original_path = f"{tool_path}_original"
            absolute_original_path = os.path.abspath(original_path)  # Resolve full absolute path

            # Rename the original binary to the new location
            os.rename(tool_path, original_path)

            # Get the original binary's permissions and ownership
            original_stat = os.stat(original_path)
            original_mode = stat.S_IMODE(original_stat.st_mode)  # File permissions
            original_uid = original_stat.st_uid  # User ID
            original_gid = original_stat.st_gid  # Group ID

            # Create the new wrapper binary in the same location
            with open(tool_path, 'w') as file:
                file.write("#!/bin/bash\n")
                file.write(f"echo \"{prefix}\"\n")
                file.write(f"{absolute_original_path} \"$@\"\n")  # Use absolute path
                file.write(f"echo \"{suffix}\"\n")

            # Set the ownership of the new wrapper binary to match the original
            shutil.chown(tool_path, user=original_uid, group=original_gid)

            # Set the permissions of the new wrapper binary to match the original
            os.chmod(tool_path, original_mode)

            self.logger.info(f"Tool wrapper with prefix and suffix created: {tool_path}")
        except Exception as e:
            self.logger.error(f"Failed to create tool wrapper: {str(e)}")

    def _remove_prefix_suffix_from_file(self, file_path, prefix, suffix):
        """
        Removes specific prefix and suffix content from a file.
        """
        try:
            # Read the entire file content as a single string
            with open(file_path, 'r') as file:
                content = file.read()

            # Remove prefix if it matches the start of the content
            if content.startswith(prefix):
                content = content[len(prefix):]

            # Remove suffix if it matches the end of the content
            if content.endswith(suffix):
                content = content[:-len(suffix)]

            # Write the updated content back to the file
            with open(file_path, 'w') as file:
                file.write(content)

            self.logger.info(f"Prefix and suffix removed from file: {file_path}")
        except Exception as e:
            self.logger.info(f"Failed to remove prefix and suffix from file: {str(e)}")


    def _restore_tool(self, tool_path):
        """
        Restores the original tool by removing the wrapper.
        """
        try:
            original_path = f"{tool_path}_original"
            if os.path.exists(original_path):
                os.rename(original_path, tool_path)
                self.logger.info(f"Restored original tool from wrapper: {tool_path}")
            else:
                self.logger.info(f"Original tool not found for wrapper: {tool_path}")
        except Exception as e:
            self.logger.info(f"Failed to restore tool: {str(e)}")
