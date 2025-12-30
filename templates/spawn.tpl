%include('./templates/header.tpl')

<script type="text/javascript">
    $(document).ready(function () 
    {
        $('#recreateButton').click(() => 
        {
            showLoadingModal('Server is re-creating. Please wait...');
        });

        $('#startButton').click(() => 
        {
            showLoadingModal('Server is starting. Please wait...');
        });

        $('#stopButton').click(() => 
        {
            showLoadingModal('Server is stopping. Please wait...');
        });

        $('#deleteButton').click(() => {
            $('#deleteConfirmModal').toggleClass('is-active');
            return false;
        });

        $('#confirmDeleteButton').click(() => {
            $('#deleteConfirmModal').toggleClass('is-active');
            showLoadingModal('Server is deleting. Please wait...');
            $('#deleteForm').submit();
        });

        $('#cancelDeleteButton').click(() => {
            $('#deleteConfirmModal').removeClass('is-active');
        });
        $(document).on('click', '.cancel-delete-btn', function() {
            $('#deleteConfirmModal').removeClass('is-active');
        });
        let streamInterval = null;
        let isStreaming = false;

        // Scroll logs to bottom on load
        function scrollLogsToBottom() {
            const logsContainer = $('#logsContainer');
            if (logsContainer.length) {
                logsContainer.scrollTop(logsContainer[0].scrollHeight);
            }
        }

        // Fetch and update logs
        function refreshLogs() {
            $.get(window.location.pathname + '/logs/content', function(data) {
                $('#logsContent').text(data);
                scrollLogsToBottom();
            }).fail(function() {
                console.error('Failed to fetch logs');
            });
        }

        // Toggle streaming
        function toggleStreaming() {
            isStreaming = !isStreaming;
            const $streamButton = $('#streamButton');
            
            if (isStreaming) {
                $streamButton.removeClass('is-outlined is-info').addClass('is-success');
                $streamButton.html('<span class="icon"><i class="fas fa-broadcast-tower"></i></span><span>Streaming</span>');
                streamInterval = setInterval(refreshLogs, 2000); // Refresh every 2 seconds
            } else {
                $streamButton.removeClass('is-success').addClass('is-outlined is-info');
                $streamButton.html('<span class="icon"><i class="fas fa-broadcast-tower"></i></span><span>Stream</span>');
                if (streamInterval) {
                    clearInterval(streamInterval);
                    streamInterval = null;
                }
            }
        }

        $('#streamButton').click(toggleStreaming);

        $('#refreshLogButton').click(() => 
        {
            $('#refreshLogButton').toggleClass('is-loading');
            refreshLogs();
            setTimeout(() => $('#refreshLogButton').removeClass('is-loading'), 1000);
        });

        // Scroll to bottom on initial load
        scrollLogsToBottom();

        // Enable streaming by default
        toggleStreaming();

        $('#modsSyncButton').click(() => 
        {
            showLoadingModal('Mods are synching and server is restarting. Please wait...');
        });
        
        $('#updateServerPropertiesButton').click(() => 
        {
            showLoadingModal('Properties are updating and server is restarting. Please wait...');
        });

        $('#replaceModsButton').click(() => 
        {
            showLoadingModal('Uploading mods and restarting server. Please wait...');
        });
        
        $('.file-input').on('change', function() 
        {
            const $fileNameDisplay = $(this).closest('.file-label').find('.file-name');
            const $form = $(this).closest('form');
            const $submitButton = $form.find('button[type="submit"]');
            
            if (this.files && this.files.length > 0) 
            {
                $fileNameDisplay.text(this.files[0].name);
                $submitButton.prop('disabled', false).removeClass('is-loading');
            } 
            else 
            {
                $fileNameDisplay.text('No file selected');
                $submitButton.prop('disabled', true);
            }
        });

        // Initialize button states on page load
        $('input.file-input').each(function() {
            const $form = $(this).closest('form');
            const $submitButton = $form.find('button[type="submit"]');
            
            if (!this.files || this.files.length === 0) {
                $submitButton.prop('disabled', true);
            }
        });
    });
</script>

<div class="container is-fluid p-4">
    <!-- Server Info Card -->
    <div class="columns is-multiline">
        <div class="column is-12-mobile is-6-tablet is-4-desktop">
            <div class="card">
                <div class="card-content">
                    <p class="title is-5">Server Info</p>
                    <table class="table is-narrow is-fullwidth">
                        <tbody>
                            <tr>
                                <td><strong>Name:</strong></td>
                                <td>{{spawn.name}}</td>
                            </tr>
                            <tr>
                                <td><strong>Status:</strong></td>
                                <td>
                                    %if spawn.get_status() == "running": 
                                        <span class="tag is-success">{{spawn.get_status()}}</span>
                                    %elif spawn.get_status() in ["created", "restarting", "removing", "paused", "exited"]:
                                        <span class="tag is-warning">{{spawn.get_status()}}</span>
                                    %else:
                                        <span class="tag is-danger">{{spawn.get_status()}}</span>
                                    %end
                                </td>
                            </tr>
                            <tr>
                                <td><strong>Port:</strong></td>
                                <td>{{spawn.port}}</td>
                            </tr>
                            <tr>
                                <td><strong>Type:</strong></td>
                                <td>{{spawn.type}}</td>
                            </tr>
                            <tr>
                                <td><strong>MC Version:</strong></td>
                                <td>{{spawn.minecraft_version}}</td>
                            </tr>
                            <tr>
                                <td><strong>Forge:</strong></td>
                                <td>{{spawn.forge_version}}</td>
                            </tr>
                            <tr>
                                <td><strong>Loaded Mods:</strong></td>
                                <td>{{len(mods)}}</td>
                            </tr>
                            %if len(spawn.pending_mod_deletions) > 0:
                            <tr>
                                <td><strong>Pending Del:</strong></td>
                                <td><span class="tag is-warning">{{len(spawn.pending_mod_deletions)}}</span></td>
                            </tr>
                            %end
                        </tbody>
                    </table>
                </div>
                <footer class="card-footer is-flex-wrap-wrap">
                    <form class="card-footer-item is-flex-grow-1" action="/spawn/{{spawn.name}}/recreate" method="post">
                        <button id="recreateButton" class="button is-info is-fullwidth">Re-create</button>
                    </form>
                    <form class="card-footer-item is-flex-grow-1" action="/spawn/{{spawn.name}}/start" method="post">
                        <button id="startButton" class="button is-success is-fullwidth">Start</button>
                    </form>
                    <form class="card-footer-item is-flex-grow-1" action="/spawn/{{spawn.name}}/stop" method="post">
                        <button id="stopButton" class="button is-warning is-fullwidth">Stop</button>
                    </form>
                    <form class="card-footer-item is-flex-grow-1" id="deleteForm" action="/spawn/{{spawn.name}}/delete" method="post">
                        <button id="deleteButton" type="button" class="button is-danger is-fullwidth">Delete</button>
                    </form>
                </footer>
            </div>
        </div>

        <!-- Mods Section -->
        <div class="column is-12-mobile is-6-tablet is-4-desktop">
            <div class="box">
                <h2 class="title is-5">Mods ({{len(mods)}})</h2>
                %if len(mods) == 0:
                <p class="has-text-grey">No mods found.</p>
                %else:
                <div style="max-height: 250px; overflow-y: auto; border: 1px solid #dbdbdb; border-radius: 4px; padding: 0.5rem;">
                %for mod in mods:
                <form action="/spawn/{{spawn.name}}/mods/delete" method="post" class="mb-1">
                    <div class="field is-grouped is-grouped-multiline mb-1">
                        <div class="control is-expanded">
                            <input class="input is-small" type="text" name="mod" value="{{mod}}" readonly>
                        </div>
                        <div class="control">
                            <button class="button is-small is-danger">Delete</button>
                        </div>
                    </div>
                </form>
                %end
                </div>
                %end

                <form action="/spawn/{{spawn.name}}/mods/replace" method="post" enctype="multipart/form-data" class="mt-3">
                    <div class="field mb-2">
                        <label class="label is-small">Replace All Mods</label>
                        <div class="file has-name is-fullwidth">
                            <label class="file-label">
                                <input class="file-input" type="file" name="mods" multiple webkitdirectory directory accept=".jar" />
                                <span class="file-cta is-small">
                                    <span class="file-icon"><i class="fas fa-folder-open"></i></span>
                                    <span class="file-label">Choose folder</span>
                                </span>
                                <span class="file-name is-small">No folder selected</span>
                            </label>
                        </div>
                    </div>
                    <button type="submit" id="replaceModsButton" class="button is-primary is-fullwidth is-small">
                        <span class="icon"><i class="fas fa-sync"></i></span>
                        <span>Replace Mods</span>
                    </button>
                </form>

                <form action="/spawn/{{spawn.name}}/mods/add-file" method="post" enctype="multipart/form-data" class="mt-3">
                    <div class="field mb-2">
                        <label class="label is-small">Add Single Mod</label>
                        <div class="file has-name is-fullwidth">
                            <label class="file-label">
                                <input class="file-input" type="file" name="mod" accept=".jar" />
                                <span class="file-cta is-small">
                                    <span class="file-icon"><i class="fas fa-upload"></i></span>
                                    <span class="file-label">Choose mod</span>
                                </span>
                                <span class="file-name is-small">No file selected</span>
                            </label>
                        </div>
                    </div>
                    <button type="submit" id="addModButton" class="button is-info is-fullwidth is-small">Add Mod</button>
                </form>
            </div>
        </div>

        <!-- Backups Section -->
        <div class="column is-12-mobile is-6-tablet is-4-desktop">
            <div class="box">
                <h2 class="title is-5">Backups</h2>
                <form action="/spawn/{{spawn.name}}/backup/create" method="post" onsubmit="showLoadingModal('Creating backup. Please wait...');">
                    <div class="field mb-2">
                        <label class="label is-small">Backup Name (optional)</label>
                        <div class="control">
                            <input class="input is-small" type="text" name="backup_name" placeholder="{{default_backup_name}}">
                        </div>
                    </div>
                    <button type="submit" class="button is-success is-fullwidth mb-3">
                        <span class="icon"><i class="fas fa-save"></i></span>
                        <span>Create Backup</span>
                    </button>
                </form>

                <h3 class="subtitle is-6">Schedule</h3>
                <form action="/spawn/{{spawn.name}}/backup/settings" method="post" onsubmit="showLoadingModal('Saving settings. Please wait...');">
                    <div class="field">
                        <label class="checkbox is-small">
                            %if spawn.backup_settings.get('daily_backup_enabled'):
                            <input type="checkbox" id="daily_backup_enabled" name="daily_backup_enabled" value="on" checked>
                            %else:
                            <input type="checkbox" id="daily_backup_enabled" name="daily_backup_enabled" value="on">
                            %end
                            <span>Enable daily backups</span>
                        </label>
                    </div>

                    <label class="label is-small">Time</label>
                    <div class="field is-grouped mb-2">
                        <div class="control is-expanded">
                            <input class="input is-small" type="number" name="daily_backup_hour" min="0" max="23" value="{{spawn.backup_settings.get('daily_backup_hour', 2)}}" placeholder="HH">
                        </div>
                        <div class="control is-expanded">
                            <input class="input is-small" type="number" name="daily_backup_minute" min="0" max="59" value="{{spawn.backup_settings.get('daily_backup_minute', 0)}}" placeholder="MM">
                        </div>
                    </div>

                    <label class="label is-small">Keep (days)</label>
                    <div class="field mb-3">
                        <div class="control is-expanded">
                            <input class="input is-small" type="number" name="retention_days" min="1" value="{{spawn.backup_settings.get('retention_days', 7)}}" placeholder="Days">
                        </div>
                    </div>

                    <button type="submit" class="button is-info is-fullwidth is-small">Save</button>
                </form>

                %if spawn.backup_settings.get('last_backup_timestamp'):
                <div class="content mt-2">
                    <small class="has-text-grey">Last: {{spawn.backup_settings.get('last_backup_timestamp')}}</small>
                </div>
                %end
            </div>
        </div>
    </div>

    <!-- Logs Section -->
    <div class="columns is-multiline mt-2">
        <div class="column is-12-mobile is-12-tablet is-6-desktop">
            <div class="box">
                <h2 class="title is-5">Logs</h2>
                <div class="buttons are-small mb-3">
                    <button id="streamButton" class="button is-outlined is-info">
                        <span class="icon"><i class="fas fa-broadcast-tower"></i></span>
                        <span>Stream</span>
                    </button>
                    <button id="refreshLogButton" type="button" class="button is-link">
                        <span class="icon"><i class="fas fa-sync"></i></span>
                        <span>Refresh</span>
                    </button>
                    <a href="/spawn/{{spawn.name}}/logs" class="button is-ghost">
                        <span class="icon"><i class="fas fa-expand"></i></span>
                        <span>Full</span>
                    </a>
                </div>
                <div id="logsContainer" style="max-height: 400px; overflow-y: auto; background: #f5f5f5; padding: 1rem; border-radius: 4px; border: 1px solid #dbdbdb;">
                    <pre id="logsContent" style="margin: 0; font-size: 0.8em; font-family: 'Courier New', monospace; white-space: pre-wrap; word-wrap: break-word;">{{spawn.logs}}</pre>
                </div>
                <form action="/spawn/{{spawn.name}}/console/send" method="post" class="mt-3">
                    <div class="field is-grouped">
                        <div class="control is-expanded">
                            <input class="input is-small" type="text" name="consoleCommand" placeholder="Console command...">
                        </div>
                        <div class="control">
                            <button class="button is-small is-link">Send</button>
                        </div>
                    </div>
                </form>
            </div>
        </div>

        <!-- Server Properties Section -->
        <div class="column is-12-mobile is-12-tablet is-6-desktop">
            <div class="box">
                <div class="level mb-3">
                    <div class="level-left">
                        <div class="level-item">
                            <h2 class="title is-5">Server Properties</h2>
                        </div>
                    </div>
                    <div class="level-right">
                        <div class="level-item">
                            <form action="/spawn/{{spawn.name}}/server_properties/save" method="post" style="display: inline;">
                                <button id="updateServerPropertiesButton" class="button is-small is-link">Update & Restart</button>
                            </form>
                        </div>
                    </div>
                </div>
                <form action="/spawn/{{spawn.name}}/server_properties/save" method="post">
                    <textarea class="textarea" name="server_properties" rows="16" style="font-family: 'Courier New', monospace; font-size: 0.85em;">{{spawn.server_properties}}</textarea>
                </form>
            </div>
        </div>
    </div>

    <!-- Backups List Section -->
    %if len(spawn.list_backups()) > 0:
    <div class="columns is-multiline mt-2">
        <div class="column is-12">
            <div class="box">
                <h2 class="title is-5">Existing Backups ({{len(spawn.list_backups())}})</h2>
                <div class="table-container">
                    <table class="table is-fullwidth is-striped">
                        <tbody>
                        %for backup in spawn.list_backups():
                            <tr>
                                <td>
                                    <div>
                                        <strong>{{backup['name']}}</strong>
                                        <br>
                                        <small class="has-text-grey">{{backup['timestamp']}} ({{backup['size_mb']}} MB)</small>
                                    </div>
                                </td>
                                <td class="is-narrow">
                                    <form action="/spawn/{{spawn.name}}/backup/restore/{{backup['name']}}" method="post" style="display: inline;" onsubmit="if(!confirm('Restore this backup? Current world will be replaced.')) return false; showLoadingModal('Restoring backup. Please wait...');return true;">
                                        <button type="submit" class="button is-small is-info">
                                            <span class="icon"><i class="fas fa-undo"></i></span>
                                        </button>
                                    </form>
                                </td>
                                <td class="is-narrow">
                                    <form action="/spawn/{{spawn.name}}/backup/delete/{{backup['name']}}" method="post" style="display: inline;" onsubmit="if(!confirm('Delete this backup?')) return false; showLoadingModal('Deleting backup. Please wait...');return true;">
                                        <button type="submit" class="button is-small is-danger">
                                            <span class="icon"><i class="fas fa-trash"></i></span>
                                        </button>
                                    </form>
                                </td>
                            </tr>
                        %end
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    %end
</div>

<!-- Delete Confirmation Modal -->
<div class="modal" id="deleteConfirmModal">
    <div class="modal-background"></div>
    <div class="modal-card">
        <header class="modal-card-head has-background-danger">
            <p class="modal-card-title has-text-white">
                <span class="icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </span>
                <span>Delete Server Confirmation</span>
            </p>
            <button class="delete cancel-delete-btn" aria-label="close"></button>
        </header>
        <section class="modal-card-body">
            <article class="message is-danger">
                <div class="message-header">
                    <p>⚠️ WARNING: This action cannot be undone!</p>
                </div>
                <div class="message-body">
                    <p class="has-text-weight-bold mb-3">You are about to permanently delete:</p>
                    <ul class="ml-5">
                        <li>✗ The entire server container</li>
                        <li>✗ All world data and player progress</li>
                        <li>✗ All mods and configurations</li>
                        <li>✗ Server properties and settings</li>
                    </ul>
                    <p class="mt-4 has-text-weight-bold">Server: <span class="has-text-danger">{{spawn.name}}</span></p>
                </div>
            </article>
        </section>
        <footer class="modal-card-foot">
            <button class="button cancel-delete-btn">Cancel</button>
            <button class="button is-danger" id="confirmDeleteButton">
                <span class="icon">
                    <i class="fas fa-trash"></i>
                </span>
                <span>Yes, Delete Permanently</span>
            </button>
        </footer>
    </div>
</div>

%include('./templates/footer.tpl')
