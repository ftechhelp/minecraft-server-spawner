%include('./templates/header.tpl')

<script type="text/javascript">
    $(document).ready(function () 
    {
        $('#recreateButton').click(() => 
        {
            $('#actionModalText').text('Server is re-creating. Please Wait...');
            $('#actionModal').toggleClass('is-active');
        });

        $('#startButton').click(() => 
        {
            $('#actionModalText').text('Server is starting. Please Wait...');
            $('#actionModal').toggleClass('is-active');
        });

        $('#stopButton').click(() => 
        {
            $('#actionModalText').text('Server is stopping. Please Wait...');
            $('#actionModal').toggleClass('is-active');
        });

        $('#deleteButton').click(() => {
            $('#deleteConfirmModal').toggleClass('is-active');
            return false; // Prevent form submission
        });

        $('#confirmDeleteButton').click(() => {
            $('#deleteConfirmModal').toggleClass('is-active');
            $('#actionModalText').text('Server is deleting. Please Wait...');
            $('#actionModal').toggleClass('is-active');
            $('#deleteForm').submit();
        });

        $('#cancelDeleteButton').click(() => {
            $('#deleteConfirmModal').removeClass('is-active');
        });
        $(document).on('click', '.cancel-delete-btn', function() {
            $('#deleteConfirmModal').removeClass('is-active');
        });
        $('#refreshLogButton').click(() => 
        {
            $('#refreshLogButton').toggleClass('is-loading');
        });

        $('#modsSyncButton').click(() => 
        {
            $('#actionModalText').text('Mods are synching and server is restarting. Please Wait...');
            $('#actionModal').toggleClass('is-active');
        });
        
        $('#updateServerPropertiesButton').click(() => 
        {
            $('#actionModalText').text('Properties are updating and server is restarting. Please Wait...');
            $('#actionModal').toggleClass('is-active');
        });

        $('#replaceModsButton').click(() => 
        {
            $('#actionModalText').text('Uploading mods and restarting server. Please Wait...');
            $('#actionModal').toggleClass('is-active');
        });
        
        // File input change handler
        $('.file-input').on('change', function() 
        {
            const $fileNameDisplay = $('#file-name-display');
            
            if (this.files && this.files[0]) 
            {
                $fileNameDisplay.text(this.files[0].name);
            } 
            else 
            {
                $fileNameDisplay.text('No file selected');
            }
        });
    });
</script>

<div class="columns m-5">
    <div class="column is-4">
        <div class="card">
            <div class="card-content">
                <p class="title">
                    <table class="table">
                        <tbody>
                            <tr>
                                <td><h4 class="subtitle is-4">Name:</h4></td>
                                <td><h4 class="subtitle is-4">{{spawn.name}}</h4></td>
                            </tr>
                            <tr>
                                <td>
                                    <h4 class="subtitle is-4">Status:</h4>
                                </td>
                                <td>
                                    %if spawn.get_status() == "running": 
                                        <h4 class="subtitle is-4 has-text-success">{{spawn.get_status()}}</h4>
                                    %elif spawn.get_status() in ["created", "restarting", "removing", "paused", "exited"]:
                                        <h4 class="subtitle is-4 has-text-warning">{{spawn.get_status()}}</h4>
                                    %else:
                                        <h4 class="subtitle is-4 has-text-danger">{{spawn.get_status()}}</h4>
                                    %end
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    <h4 class="subtitle is-4">Port:</h4>
                                </td>
                                <td>
                                    <h4 class="subtitle is-4">{{spawn.port}}</h4>
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    <h4 class="subtitle is-4">Type:</h4>
                                </td>
                                <td>
                                    <h4 class="subtitle is-4">{{spawn.type}}</h4>
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    <h4 class="subtitle is-4">Minecraft Version:</h4>
                                </td>
                                <td>
                                    <h4 class="subtitle is-4">{{spawn.minecraft_version}}</h4>
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    <h4 class="subtitle is-4">Forge Version:</h4>
                                </td>
                                <td>
                                    <h4 class="subtitle is-4">{{spawn.forge_version}}</h4>
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    <h4 class="subtitle is-4">Loaded Mods:</h4>
                                </td>
                                <td>
                                    <h4 class="subtitle is-4">{{len(mods)}}</h4>
                                </td>
                            </tr>
                            %if len(spawn.pending_mod_deletions) > 0:
                            <tr>
                                <td>
                                    <h4 class="subtitle is-4">Pending Deletions:</h4>
                                </td>
                                <td>
                                    <h4 class="subtitle is-4 has-text-warning">{{len(spawn.pending_mod_deletions)}} (restart required)</h4>
                                </td>
                            </tr>
                            %end
                        </tbody>
                    </table>
                </p>
            </div>
            <footer class="card-footer">
                <form class="card-footer-item" action="/spawn/{{spawn.name}}/recreate" method="post">
                    <button id="recreateButton" class="">Re-create</button>
                </form>
                <form class="card-footer-item" action="/spawn/{{spawn.name}}/start" method="post">
                    <button id="startButton" class="">Start</button>
                </form>
                <form class="card-footer-item" action="/spawn/{{spawn.name}}/stop" method="post">
                    <button id="stopButton" class="">Stop</button>
                </form>
                <form class="card-footer-item" id="deleteForm" action="/spawn/{{spawn.name}}/delete" method="post">
                    <button id="deleteButton" type="button" class="button is-danger is-fullwidth">Delete</button>
                </form>
            </footer>
        </div>
        <label class="label">Mods</label>
        %if len(mods) == 0:
        <p class="has-text-grey">No mods found in data/mods.</p>
        %else:
        %for mod in mods:
        <form action="/spawn/{{spawn.name}}/mods/delete" method="post">
            <div class="field has-addons p-1">
                <div class="control is-expanded">
                    <input class="input" type="text" name="mod" value="{{mod}}" readonly>
                </div>
                <div class="control">
                    <button class="button is-danger">Delete</button>
                </div>
            </div>
        </form>
        %end
        %end

        <!-- Replace entire mods folder by uploading a local folder -->
        <form action="/spawn/{{spawn.name}}/mods/replace" method="post" enctype="multipart/form-data">
            <div class="field has-addons pb-3">
                <div class="control is-expanded">
                    <div class="file has-name is-fullwidth">
                        <label class="file-label">
                            <input class="file-input" type="file" name="mods" multiple webkitdirectory directory accept=".jar" />
                            <span class="file-cta">
                                <span class="file-icon">
                                    <i class="fas fa-folder-open"></i>
                                </span>
                                <span class="file-label"> Choose mods folder </span>
                            </span>
                            <span class="file-name" id="file-name-display"> No folder selected </span>
                        </label>
                    </div>
                </div>
                <div class="control">
                    <button type="submit" id="replaceModsButton" class="button is-primary">
                        <span class="icon"><i class="fas fa-sync"></i></span>
                        <span>Replace Mods</span>
                    </button>
                </div>
            </div>
        </form>

        <!-- Add single mod file -->
        <form action="/spawn/{{spawn.name}}/mods/add-file" method="post" enctype="multipart/form-data">
            <div class="field has-addons p-1">
                <div class="control is-expanded">
                    <div class="file has-name is-fullwidth">
                        <label class="file-label">
                            <input class="file-input" type="file" name="mod" accept=".jar" />
                            <span class="file-cta">
                                <span class="file-icon"><i class="fas fa-upload"></i></span>
                                <span class="file-label"> Choose mod (.jar) </span>
                            </span>
                            <span class="file-name" id="file-name-display"> No file selected </span>
                        </label>
                    </div>
                </div>
                <div class="control">
                    <button class="button is-info">Add Mod</button>
                </div>
            </div>
        </form>

        <!-- Backups Section -->
        <label class="label">Backups</label>
        <form action="/spawn/{{spawn.name}}/backup/create" method="post">
            <div class="field p-1">
                <button type="submit" class="button is-success is-fullwidth">
                    <span class="icon"><i class="fas fa-save"></i></span>
                    <span>Create Backup Now</span>
                </button>
            </div>
        </form>

        <!-- Backup Settings -->
        <label class="label">Backup Schedule & Retention</label>
        <form action="/spawn/{{spawn.name}}/backup/settings" method="post">
            <div class="field">
                <label class="checkbox">
                    <input type="checkbox" name="daily_backup_enabled" %if spawn.backup_settings.get('daily_backup_enabled') %}checked%end %>>
                    Enable daily automated backups
                </label>
            </div>

            <div class="columns">
                <div class="column is-6">
                    <label class="label is-small">Backup Time (24h)</label>
                    <div class="field has-addons">
                        <div class="control is-expanded">
                            <input class="input" type="number" name="daily_backup_hour" min="0" max="23" value="{{spawn.backup_settings.get('daily_backup_hour', 2)}}" placeholder="Hour (0-23)">
                        </div>
                        <div class="control is-expanded">
                            <input class="input" type="number" name="daily_backup_minute" min="0" max="59" value="{{spawn.backup_settings.get('daily_backup_minute', 0)}}" placeholder="Minute (0-59)">
                        </div>
                    </div>
                </div>

                <div class="column is-6">
                    <label class="label is-small">Keep Backups For (days)</label>
                    <div class="control">
                        <input class="input" type="number" name="retention_days" min="1" value="{{spawn.backup_settings.get('retention_days', 7)}}" placeholder="Days">
                    </div>
                </div>
            </div>

            <div class="control">
                <button type="submit" class="button is-info is-fullwidth">Save Backup Settings</button>
            </div>

            %if spawn.backup_settings.get('last_backup_timestamp'):
            <div class="content mt-3">
                <small class="has-text-grey">Last backup: {{spawn.backup_settings.get('last_backup_timestamp', 'Never')}}</small>
            </div>
            %end
        </form>

        <!-- Backup List -->
        %if len(spawn.list_backups()) == 0:
        <p class="has-text-grey mt-3">No backups found.</p>
        %else:
        <label class="label mt-5">Existing Backups</label>
        <div class="box p-3">
            %for backup in spawn.list_backups():
            <div class="level is-mobile mb-3 pb-3" style="border-bottom: 1px solid #dbdbdb;">
                <div class="level-left">
                    <div class="level-item">
                        <div>
                            <p class="heading">{{backup['name']}}</p>
                            <p class="title is-6">{{backup['timestamp']}} ({{backup['size_mb']}} MB)</p>
                        </div>
                    </div>
                </div>
                <div class="level-right">
                    <div class="level-item">
                        <form action="/spawn/{{spawn.name}}/backup/restore/{{backup['name']}}" method="post" style="display: inline;">
                            <button type="submit" class="button is-small is-info" onclick="return confirm('Restore this backup? Current world will be replaced.');">
                                <span class="icon is-small"><i class="fas fa-undo"></i></span>
                                <span>Restore</span>
                            </button>
                        </form>
                    </div>
                    <div class="level-item">
                        <form action="/spawn/{{spawn.name}}/backup/delete/{{backup['name']}}" method="post" style="display: inline;">
                            <button type="submit" class="button is-small is-danger" onclick="return confirm('Delete this backup?');">
                                <span class="icon is-small"><i class="fas fa-trash"></i></span>
                                <span>Delete</span>
                            </button>
                        </form>
                    </div>
                </div>
            </div>
            %end
        </div>
        %end
    </div>
    <div class="column is-8">
        <article class="message">
            <div class="message-header">
                <p class="subtitle is-4">Logs</p>
                <div class="is-4 is-flex is-align-items-flex-end">
                    <form action="/spawn/{{spawn.name}}/refresh" method="post">
                        <button id="refreshLogButton" class="button is-link">Refresh</button>
                    </form>
                    <a href="/spawn/{{spawn.name}}/logs" class="button is-ghost ml-2">Full Logs</a>
                </div>
            </div>
            <div class="message-body">
                <pre>{{spawn.logs}}</pre>
                <form action="/spawn/{{spawn.name}}/console/send" method="post" class="pt-4">
                    <div class="field has-addons">
                        <div class="control is-expanded">
                            <input class="input" type="text" name="consoleCommand" placeholder="Enter Console Command">
                        </div>
                        <div class="control">
                            <button class="button is-link">
                                Send
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </article>
        <form action="/spawn/{{spawn.name}}/server_properties/save" method="post">
            <article class="message">
                <div class="message-header">
                    <p class="subtitle is-4">Server Properties</p>
                    <div class="is-4 is-flex is-align-items-flex-end">
                        <button id="updateServerPropertiesButton" class="button is-link">Update & Restart</button>
                    </div>
                </div>
                <div class="message-body">
                    <textarea class="textarea is-info" name="server_properties" rows="20">
                        {{spawn.server_properties}}
                    </textarea>
                </div>
            </article>
        </form>
    </div>
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