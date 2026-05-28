%include('./templates/header.tpl')

<script type="text/javascript">
    $(document).ready(function () {
        $('.open-delete-modal').click(function () {
            const backupFile = $(this).data('backup-file');
            $('#deleteBackupFile').val(backupFile);
            $('#deleteBackupName').text(backupFile);
            $('#deleteArchivedModal').addClass('is-active');
        });

        $('.close-delete-modal').click(function () {
            $('#deleteArchivedModal').removeClass('is-active');
        });
    });
</script>

<section class="section">
    <div class="container">
        <div class="level">
            <div class="level-left">
                <div class="level-item">
                    <h1 class="title is-3">Archived Backups</h1>
                </div>
            </div>
        </div>

        <p class="subtitle is-6">Backups in this page are preserved in the root <code>backups</code> folder and survive spawn deletion.</p>

        %if notice:
        <div class="notification is-success is-light">
            {{notice}}
        </div>
        %end

        %if page_error:
        <div class="notification is-danger is-light">
            {{page_error}}
        </div>
        %end

        %if len(archived_backups) == 0:
        <div class="box">
            <p class="has-text-grey">No archived backups found yet.</p>
            <p class="has-text-grey">Delete a spawn after taking a backup to archive its latest backup here.</p>
        </div>
        %else:
        <div class="box">
            <div class="table-container">
                <table class="table is-fullwidth is-striped is-hoverable">
                    <thead>
                        <tr>
                            <th>Backup File</th>
                            <th>Source Server</th>
                            <th>Server Type</th>
                            <th>MC Version</th>
                            <th>Mod Loader Version</th>
                            <th>Created At</th>
                            <th>Size</th>
                            <th>Restore</th>
                            <th>Delete</th>
                        </tr>
                    </thead>
                    <tbody>
                        %for backup in archived_backups:
                        <tr>
                            <td><code>{{backup['file']}}</code></td>
                            <td>{{backup['source_server']}}</td>
                            <td>{{backup['server_type']}}</td>
                            <td>{{backup['minecraft_version']}}</td>
                            <td>{{backup['forge_version']}}</td>
                            <td>{{backup['timestamp']}}</td>
                            <td>{{backup['size_mb']}} MB</td>
                            <td>
                                <form method="post" action="/backups/restore" class="is-flex is-align-items-center" style="gap: 0.5rem;" onsubmit="showLoadingModal('Please wait while we restore your server...'); return true;">
                                    <input type="hidden" name="backup_file" value="{{backup['file']}}">
                                    <input class="input is-small" type="text" name="restored_name" placeholder="New server name (optional)">
                                    <button type="submit" class="button is-small is-link">
                                        <span class="icon"><i class="fas fa-undo"></i></span>
                                        <span>Restore</span>
                                    </button>
                                </form>
                            </td>
                            <td>
                                <button type="button" class="button is-small is-danger open-delete-modal" data-backup-file="{{backup['file']}}">
                                    <span class="icon"><i class="fas fa-trash"></i></span>
                                    <span>Delete</span>
                                </button>
                            </td>
                        </tr>
                        %end
                    </tbody>
                </table>
            </div>
        </div>
        %end
    </div>
</section>

<div class="modal" id="deleteArchivedModal">
    <div class="modal-background close-delete-modal"></div>
    <div class="modal-card">
        <header class="modal-card-head has-background-danger">
            <p class="modal-card-title has-text-white">Delete archived backup</p>
            <button class="delete close-delete-modal" aria-label="close"></button>
        </header>
        <section class="modal-card-body">
            <article class="message is-danger is-light">
                <div class="message-body">
                    <p class="has-text-weight-semibold mb-2">This will permanently delete the archived backup.</p>
                    <p>Backup: <code id="deleteBackupName"></code></p>
                    <p class="mt-2">This action cannot be undone.</p>
                </div>
            </article>
        </section>
        <footer class="modal-card-foot">
            <button type="button" class="button close-delete-modal">Cancel</button>
            <form method="post" action="/backups/delete">
                <input type="hidden" name="backup_file" id="deleteBackupFile" value="">
                <button type="submit" class="button is-danger">
                    <span class="icon"><i class="fas fa-trash"></i></span>
                    <span>Delete permanently</span>
                </button>
            </form>
        </footer>
    </div>
</div>

%include('./templates/footer.tpl')
