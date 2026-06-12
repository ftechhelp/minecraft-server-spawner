%include('./templates/header.tpl')

<section class="section">
    <div class="container">
        <div class="content">
            <h1 class="title is-1">User Documentation</h1>
            <p class="subtitle">Complete guide for every page, every main action, and the most common recovery workflows in this app</p>

            <div class="notification is-info">
                <p><strong>Web panel:</strong> <code>{{web_panel_url}}</code></p>
                <p><strong>Minecraft connection format:</strong> <code>{{server_connection_host}}:PORT</code></p>
                <p><strong>Example:</strong> <code>{{server_connection_example}}</code></p>
            </div>

            <section class="box">
                <h2 class="title is-4">
                    <span class="icon has-text-link"><i class="fa-solid fa-circle-question"></i></span>
                    Ask the docs
                </h2>
                <p>Ask a question and Gemini answers it from this documentation, so you don't have to search through the page.</p>
                <form id="docsAskForm">
                    <div class="field has-addons">
                        <div class="control is-expanded">
                            <input id="docsQuestion" class="input" type="text" maxlength="500" placeholder="e.g. How do I restore a server I deleted?">
                        </div>
                        <div class="control">
                            <button type="submit" id="docsAskButton" class="button is-link">
                                <span class="icon"><i class="fa-solid fa-paper-plane"></i></span>
                                <span>Ask</span>
                            </button>
                        </div>
                    </div>
                </form>
                <div id="docsAnswer" class="notification is-hidden mt-3" style="white-space: pre-wrap;"></div>
            </section>

            <script type="text/javascript">
                $(document).ready(function() {
                    $('#docsAskForm').on('submit', function(event) {
                        event.preventDefault();
                        const question = $('#docsQuestion').val().trim();
                        if (!question) {
                            return;
                        }
                        const $button = $('#docsAskButton');
                        const $answer = $('#docsAnswer');
                        $button.addClass('is-loading').prop('disabled', true);
                        $answer.removeClass('is-hidden is-danger').text('Thinking...');

                        fetch('/docs/ask', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                            body: new URLSearchParams({ question })
                        })
                            .then(async (response) => {
                                const payload = await response.json().catch(() => ({}));
                                if (!response.ok || !payload.ok) {
                                    throw new Error(payload.error || 'The question could not be answered.');
                                }
                                $answer.text(payload.answer);
                            })
                            .catch((error) => {
                                $answer.addClass('is-danger').text(error.message);
                            })
                            .finally(() => {
                                $button.removeClass('is-loading').prop('disabled', false);
                            });
                    });
                });
            </script>

            <section class="box">
                <h2 class="title is-3">What this app does</h2>
                <p>This panel lets you create, run, inspect, back up, restore, and delete Minecraft servers from a web interface. Each server is managed as its own Docker-based spawn with its own data folder, logs, mods folder, and backup history.</p>
                <p>The app currently supports three server types:</p>
                <ul>
                    <li><strong>VANILLA</strong> for unmodded servers</li>
                    <li><strong>FORGE</strong> for modded Forge servers</li>
                    <li><strong>NEOFORGE</strong> for modded NeoForge servers (Minecraft 1.20.1+)</li>
                </ul>
                <p>From the UI you can create a server, start and stop it, recreate its container, edit <code>server.properties</code>, upload mods, send console commands, view logs, analyze logs, create backups, restore backups, and recover archived backups after a server has been deleted.</p>
            </section>

            <section class="box">
                <h2 class="title is-3">Quick Start</h2>
                <ol>
                    <li>Open <strong>Home</strong> from the navbar.</li>
                    <li>Create a new server with a name, port, type, and version choices.</li>
                    <li>Open the new server page.</li>
                    <li>Wait for the status to become <strong>running</strong>.</li>
                    <li>Watch the logs until startup finishes and the server is ready.</li>
                    <li>Copy the connection address shown on the server page.</li>
                    <li>Join from Minecraft using <code>{{server_connection_host}}:PORT</code>.</li>
                    <li>Create a manual backup before making major changes.</li>
                </ol>
            </section>

            <section class="box">
                <h2 class="title is-3">Accounts, login and eggs <span class="icon has-text-warning"><i class="fa-solid fa-egg"></i></span></h2>
                <p>Every account has a balance of <strong>eggs</strong> — the panel's "spawns" currency. Your egg count is how many servers you may have <strong>running at the same time</strong>. Eggs are never spent: stopping or deleting a server frees its egg automatically. The navbar shows your eggs — cracked-open eggs are in use, whole eggs are free.</p>

                <h3 class="title is-5">Not logged in?</h3>
                <p>You can still browse everything, and you can create servers — they are <em>unowned</em>. All anonymous visitors share a single egg, so only one unowned server can run at a time. Unowned servers can be managed by anyone.</p>

                <h3 class="title is-5">Logged in</h3>
                <p>The first time you log in, the panel asks you to set your own password before you can do anything else — the password your account was created with is only temporary.</p>
                <p>Servers you create belong to you. Only you and admins can start, stop, delete, or change them; other visitors see them read-only. Need more eggs? Ask an admin.</p>
                <p>You can also <strong>claim</strong> an unowned server to take ownership of it — use the <strong>Claim</strong> button on its dashboard card or the banner on its detail page. Claiming a server that is currently running requires a free egg, because the server moves off the shared anonymous egg and onto one of yours.</p>

                <h3 class="title is-5">Admins</h3>
                <p>Admins have an <strong>Admin</strong> link in the navbar leading to user management: create or delete users, set egg balances, and grant or revoke admin. Deleting a user makes their servers unowned. The last admin cannot be deleted or demoted. The first admin account is created from the <code>ADMIN_USERNAME</code> and <code>ADMIN_PASSWORD</code> environment variables on first start.</p>
            </section>

            <section class="box">
                <h2 class="title is-3">Navigation and pages</h2>
                <p>The top navigation bar is available on all normal pages. It links to <strong>Home</strong>, <strong>Documentation</strong>, <strong>Archived Backups</strong>, and an external <strong>Report an issue</strong> page on GitHub.</p>
                <div class="table-container">
                    <table class="table is-fullwidth is-striped">
                        <thead>
                            <tr>
                                <th>Page</th>
                                <th>Route</th>
                                <th>Purpose</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>Home</strong></td>
                                <td><code>/</code></td>
                                <td>Create new servers and browse existing spawns.</td>
                            </tr>
                            <tr>
                                <td><strong>Documentation</strong></td>
                                <td><code>/docs</code></td>
                                <td>This guide.</td>
                            </tr>
                            <tr>
                                <td><strong>Archived Backups</strong></td>
                                <td><code>/backups</code></td>
                                <td>Manage backups preserved after a server has been deleted.</td>
                            </tr>
                            <tr>
                                <td><strong>Spawn details</strong></td>
                                <td><code>/spawn/&lt;name&gt;</code></td>
                                <td>Manage a single server in detail.</td>
                            </tr>
                            <tr>
                                <td><strong>Full logs</strong></td>
                                <td><code>/spawn/&lt;name&gt;/logs</code></td>
                                <td>Open a full-page log view for a server.</td>
                            </tr>
                            <tr>
                                <td><strong>Error pages</strong></td>
                                <td><code>404</code> / <code>500</code></td>
                                <td>Show friendly errors plus details you can send for support.</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>

            <section class="box">
                <h2 class="title is-3">Home page</h2>
                <p>The home page is a dashboard with three areas:</p>
                <ul>
                    <li>A stats bar with total servers, how many are running, total players online, and eggs in use</li>
                    <li>A card grid showing every server with its status, type, versions, port, owner, player count, and quick actions</li>
                    <li>A create-server dialog, opened with the <strong>+ New Server</strong> button</li>
                </ul>

                <h3 class="title is-5">Create server form</h3>
                <p>Click <strong>+ New Server</strong> to open the form. It accepts these values:</p>
                <ul>
                    <li><strong>Name</strong> - optional. If left blank, the app generates a random UUID-style name.</li>
                    <li><strong>Port</strong> - optional. If left blank, the app assigns the next available port in the allowed range.</li>
                    <li><strong>Type</strong> - choose <strong>FORGE</strong>, <strong>NEOFORGE</strong>, or <strong>VANILLA</strong>.</li>
                    <li><strong>Minecraft version</strong> - accepts <code>LATEST</code>, <code>X.Y</code>, or <code>X.Y.Z</code>.</li>
                    <li><strong>Forge/NeoForge version</strong> - accepts <code>LATEST</code>, <code>X.Y.Z</code>, or <code>X.Y.Z.W</code> for Forge and NeoForge servers. NeoForge also accepts <code>beta</code>.</li>
                </ul>

                <h3 class="title is-5">Validation rules</h3>
                <ul>
                    <li>Spawn names can only contain letters, numbers, hyphens, and underscores.</li>
                    <li>Spawn names cannot contain path traversal characters such as <code>..</code>, <code>/</code>, or <code>\</code>.</li>
                    <li>Spawn names must be unique.</li>
                    <li>Existing spawn directories on disk are also blocked from reuse.</li>
                    <li>Ports must be between <code>25565</code> and <code>25665</code>.</li>
                    <li>Ports already used by another spawn are blocked.</li>
                    <li>If no free port remains in the allowed range, server creation fails.</li>
                    <li>Only <strong>FORGE</strong>, <strong>NEOFORGE</strong>, and <strong>VANILLA</strong> are accepted as server types.</li>
                </ul>

                <h3 class="title is-5">Server cards</h3>
                <p>Each server has a card showing its name (linked to the detail page), type, Minecraft and mod loader versions, port, owner, and a color-coded status tag:</p>
                <ul>
                    <li><strong>Green</strong> for <code>running</code></li>
                    <li><strong>Yellow</strong> for transitional states such as <code>created</code>, <code>restarting</code>, <code>removing</code>, <code>paused</code>, or <code>exited</code></li>
                    <li><strong>Red</strong> for other failure or unavailable states</li>
                </ul>
                <p>Status tags, per-server player counts, and the stats bar refresh automatically every 10 seconds without reloading the page.</p>
                <p>Each card has a <strong>Manage</strong> link to the detail page, plus a quick <strong>Start</strong> or <strong>Stop</strong> button when you have permission to manage that server (you own it, you are an admin, or it is unowned). Starting a server from the dashboard still requires a free egg.</p>

                <h3 class="title is-5">Create form errors</h3>
                <p>If server creation fails validation, the page shows an error notification at the top and keeps the values you already entered so you can correct only the problem field.</p>
            </section>

            <section class="box">
                <h2 class="title is-3">Spawn detail page</h2>
                <p>The spawn detail page is the main working area for an individual server. It combines live status, connection information, mods, backups, logs, console access, and property editing.</p>

                <h3 class="title is-5">Server info card</h3>
                <ul>
                    <li><strong>Name</strong> - the spawn name used by this app.</li>
                    <li><strong>Status</strong> - automatically refreshed every few seconds.</li>
                    <li><strong>Port</strong> - the external game port players should use.</li>
                    <li><strong>Players Online</strong> - shown when the server responds to status queries.</li>
                    <li><strong>Connect</strong> - the game address plus a copy button.</li>
                    <li><strong>Type</strong> - <code>FORGE</code>, <code>NEOFORGE</code>, or <code>VANILLA</code>.</li>
                    <li><strong>MC Version</strong> - the configured Minecraft version.</li>
                    <li><strong>Forge / NeoForge</strong> - the configured mod loader version (label adapts to the server type).</li>
                    <li><strong>Loaded Mods</strong> - number of files currently in the mods folder.</li>
                    <li><strong>Pending Del</strong> - appears when one or more mods were deleted from disk but the server has not yet been restarted to fully apply the change.</li>
                </ul>

                <h3 class="title is-5">Main server actions</h3>
                <div class="table-container">
                    <table class="table is-fullwidth is-striped">
                        <thead>
                            <tr>
                                <th>Action</th>
                                <th>What it does</th>
                                <th>When to use it</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>Re-create</strong></td>
                                <td>Rebuilds and recreates the spawn container using the current spawn configuration.</td>
                                <td>Use after changing mods, after changing <code>server.properties</code>, or when a container needs a clean restart.</td>
                            </tr>
                            <tr>
                                <td><strong>Start</strong></td>
                                <td>Starts a stopped container.</td>
                                <td>Use when the server is stopped and you want it online again.</td>
                            </tr>
                            <tr>
                                <td><strong>Stop</strong></td>
                                <td>Stops the server container.</td>
                                <td>Use before risky operations or when you want the server offline.</td>
                            </tr>
                            <tr>
                                <td><strong>Delete</strong></td>
                                <td>Permanently removes the live spawn container and its files.</td>
                                <td>Use only when you are done with the server or have already protected the data you need.</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="notification is-warning">
                    <p><strong>Important:</strong> deleting a spawn removes the live server files. Before deletion, the app attempts to archive the latest backup into the root archived backups area.</p>
                </div>
            </section>

            <section class="box">
                <h2 class="title is-3">Connecting players</h2>
                <ol>
                    <li>Open the spawn detail page.</li>
                    <li>Confirm the server status is <strong>running</strong>.</li>
                    <li>Copy the connection address shown in the server info card.</li>
                    <li>Give players the address in the form <code>{{server_connection_host}}:PORT</code>.</li>
                    <li>From Minecraft Java Edition, open <strong>Multiplayer</strong> and paste the address into the server entry.</li>
                </ol>

                <p>The host portion of the address comes from the configured <code>SERVER_CONNECTION_HOST</code> environment variable. Players always use that host plus the spawn port.</p>
            </section>

            <section class="box">
                <h2 class="title is-3">Mods management</h2>
                <p>The mods section is available on every spawn page. It works best for Forge-oriented workflows.</p>

                <h3 class="title is-5">What you can do</h3>
                <ul>
                    <li>See the current list of mod files in the server's mods folder</li>
                    <li>Delete an existing mod file</li>
                    <li>Add a single <code>.jar</code> mod file</li>
                    <li>Replace the full mods folder by selecting a folder of <code>.jar</code> files</li>
                </ul>

                <h3 class="title is-5">Add Single Mod</h3>
                <ol>
                    <li>Choose one <code>.jar</code> file.</li>
                    <li>Click <strong>Add Mod</strong>.</li>
                    <li>The page shows live upload progress with percentage, transferred size, speed, and estimated time remaining while the file is being sent.</li>
                    <li>The file is saved into the mods folder.</li>
                    <li>The server performs a lightweight restart so the new mod is applied.</li>
                </ol>

                <p>After the upload reaches 100%, the page switches to a processing state while the server applies the mod and restarts.</p>

                <h3 class="title is-5">Replace All Mods</h3>
                <ol>
                    <li>Choose a folder containing the mod files you want to use.</li>
                    <li>Click <strong>Replace Mods</strong>.</li>
                    <li>The page shows live upload progress with percentage, transferred size, speed, and estimated time remaining while the files are being sent.</li>
                    <li>The browser uploads the selected <code>.jar</code> files to a temporary server-side batch in smaller requests instead of sending the whole folder in one large request.</li>
                    <li>After all files are staged, the app commits the batch as one full mods replacement.</li>
                    <li>The app swaps the full mods folder in one step instead of deleting old mods one by one.</li>
                    <li>The app performs a lightweight server restart to apply the new set.</li>
                </ol>

                <p>This flow is optimized for larger mod batches and is much faster when replacing packs with 100 or more mods.</p>
                <p>The time estimate reflects the browser upload stage. After the upload reaches 100%, the page switches to a processing state while the server applies the new mods and restarts.</p>

                <h3 class="title is-5">Delete a mod</h3>
                <ol>
                    <li>Click <strong>Delete</strong> beside the mod file.</li>
                    <li>The file is removed immediately from disk.</li>
                    <li>The app records the mod as a pending deletion.</li>
                    <li>Restart or recreate the server to fully apply the removal.</li>
                </ol>

                <h3 class="title is-5">Delete All Mods</h3>
                <ol>
                    <li>Click <strong>Delete All Mods</strong> in the mods section.</li>
                    <li>Confirm the action in the dialog.</li>
                    <li>The app removes all current mod files from disk in one operation.</li>
                    <li>The app records those files as pending deletions.</li>
                    <li>Restart or recreate the server to fully apply the removal.</li>
                </ol>

                <div class="notification is-warning">
                    <p><strong>Important:</strong> only files ending in <code>.jar</code> are accepted for upload.</p>
                    <p><strong>Tip:</strong> always create a backup before changing your mod set.</p>
                </div>
            </section>

            <section class="box">
                <h2 class="title is-3">Backups on the spawn page</h2>
                <p>Each spawn keeps its own local backups. These are separate from the archived backups page.</p>

                <h3 class="title is-5">Manual backups</h3>
                <ul>
                    <li>You can create a backup with an optional custom name.</li>
                    <li>If you leave the name blank, the app shows and uses a timestamp-based name.</li>
                    <li>Manual backups are saved in the spawn's own backups directory.</li>
                    <li>The backup captures the spawn contents, excluding the backups folder itself.</li>
                </ul>

                <h3 class="title is-5">Scheduled backups</h3>
                <ul>
                    <li>You can enable or disable daily backups per spawn.</li>
                    <li>You can choose the daily backup hour and minute.</li>
                    <li>You can choose how many days of backups to keep.</li>
                    <li>The scheduler uses the app timezone <code>America/Vancouver</code>.</li>
                    <li>The scheduler checks regularly and creates one daily backup per day when enabled.</li>
                </ul>

                <h3 class="title is-5">Existing backups list</h3>
                <p>When backups exist, the spawn page shows a list with:</p>
                <ul>
                    <li>backup filename</li>
                    <li>whether the backup is <strong>Manual</strong> or <strong>Daily</strong></li>
                    <li>timestamp</li>
                    <li>size</li>
                    <li>restore action</li>
                    <li>delete action</li>
                </ul>

                <h3 class="title is-5">Restore a spawn-local backup</h3>
                <ol>
                    <li>Click the restore button beside the backup.</li>
                    <li>Confirm the restore.</li>
                    <li>The current server is stopped.</li>
                    <li>The current <code>data</code> directory is removed.</li>
                    <li>The backup is extracted into the spawn directory.</li>
                    <li>The app rewrites the compose settings so the spawn keeps its current name, port, and configured versions.</li>
                    <li>The server is recreated and started again.</li>
                </ol>

                <div class="notification is-danger">
                    <p><strong>Restore warning:</strong> restoring a backup replaces the current live world and data for that spawn.</p>
                </div>
            </section>

            <section class="box">
                <h2 class="title is-3">Archived Backups page</h2>
                <p>The <strong>Archived Backups</strong> page is for preserved backups that survive server deletion.</p>

                <h3 class="title is-5">How backups get archived</h3>
                <ul>
                    <li>When you delete a spawn, the app tries to archive the latest available backup first.</li>
                    <li>If a latest backup exists, it is copied into the root archived backups folder.</li>
                    <li>Metadata is saved with the archived backup, including source server, server type, Minecraft version, and Forge version.</li>
                </ul>

                <h3 class="title is-5">What the archived backups table shows</h3>
                <ul>
                    <li>backup file name</li>
                    <li>source server</li>
                    <li>server type</li>
                    <li>Minecraft version</li>
                    <li>Forge version</li>
                    <li>creation timestamp</li>
                    <li>file size</li>
                </ul>

                <h3 class="title is-5">Restore an archived backup</h3>
                <ol>
                    <li>Open <strong>Archived Backups</strong>.</li>
                    <li>Find the backup you want.</li>
                    <li>Optionally provide a new server name.</li>
                    <li>Click <strong>Restore</strong>.</li>
                    <li>The app creates a brand new spawn using the backup metadata.</li>
                    <li>If the requested name already exists, the app automatically chooses a unique variation.</li>
                    <li>The app assigns the next available port.</li>
                    <li>The backup is copied into that new spawn and restored into it.</li>
                    <li>If restore succeeds, you are redirected to the new spawn page.</li>
                </ol>

                <h3 class="title is-5">Delete an archived backup</h3>
                <p>Use the delete button to remove the archived backup permanently. A confirmation modal is shown first.</p>

                <div class="notification is-warning">
                    <p><strong>Important:</strong> archived backups are your recovery points after live server deletion.</p>
                </div>

                <div class="notification is-danger">
                    <p><strong>Permanent action:</strong> deleting an archived backup cannot be undone.</p>
                </div>
            </section>

            <section class="box">
                <h2 class="title is-3">Logs, log streaming, and AI analysis</h2>
                <p>The logs section on the spawn page is one of the most useful places for troubleshooting.</p>

                <h3 class="title is-5">What you can do</h3>
                <ul>
                    <li><strong>Analyze</strong> - request an AI-assisted explanation of the current logs</li>
                    <li><strong>Stream</strong> - toggle live log refresh on and off</li>
                    <li><strong>Refresh</strong> - manually reload the current log view</li>
                    <li><strong>Full</strong> - open a full-page log view</li>
                </ul>

                <h3 class="title is-5">What to expect</h3>
                <ul>
                    <li>Streaming is enabled by default when you open a spawn page.</li>
                    <li>The main page log area refreshes every few seconds while streaming is active.</li>
                    <li>The app converts Docker log timestamps into the Vancouver timezone for display.</li>
                    <li>If the server has not produced logs yet, the log area may show <code>No logs available.</code></li>
                </ul>

                <h3 class="title is-5">AI log analysis</h3>
                <ul>
                    <li>The <strong>Analyze</strong> button sends the current logs to the configured Gemini model.</li>
                    <li>If Gemini is configured, the app shows a modal with a summary and likely issue details.</li>
                    <li>If Gemini is not configured, the analysis action returns a configuration error instead of a summary.</li>
                </ul>
            </section>

            <section class="box">
                <h2 class="title is-3">Console commands</h2>
                <p>The console input on the spawn page lets you send commands directly to the running Minecraft container.</p>
                <p>Examples include common administrative or gameplay commands such as:</p>
                <ul>
                    <li><code>list</code></li>
                    <li><code>say Server maintenance in 5 minutes</code></li>
                    <li><code>time set day</code></li>
                    <li><code>whitelist add playername</code></li>
                    <li><code>save-all</code></li>
                </ul>
                <div class="notification is-warning">
                    <p><strong>Important:</strong> only send commands you would normally trust on a live Minecraft server. The app does not add a confirmation step for console commands.</p>
                </div>
            </section>

            <section class="box">
                <h2 class="title is-3">Server Properties editor</h2>
                <p>The <strong>Server Properties</strong> section shows the contents of <code>server.properties</code> for the current spawn.</p>
                <ul>
                    <li>Edit the text directly in the textarea.</li>
                    <li>Click <strong>Update &amp; Restart</strong> to save and recreate the container.</li>
                    <li>If the file does not exist yet for a brand new server, the editor may initially be empty.</li>
                    <li>This is normal for newly created servers before their first full startup finishes.</li>
                </ul>
            </section>

            <section class="box">
                <h2 class="title is-3">Full logs page</h2>
                <p>The full logs page opens a dedicated page containing the server logs in a monospace block. Use it when you want a larger reading area or want to copy a longer chunk of logs. This page is read-only.</p>
            </section>

            <section class="box">
                <h2 class="title is-3">Loading and confirmation behavior</h2>
                <ul>
                    <li>Long-running actions show a loading modal.</li>
                    <li>Deleting a spawn opens a dedicated confirmation modal.</li>
                    <li>Deleting an archived backup also opens a confirmation modal.</li>
                    <li>Restoring or deleting a local spawn backup uses browser confirmation prompts.</li>
                </ul>
            </section>

            <section class="box">
                <h2 class="title is-3">Error pages</h2>
                <p>The app includes friendly error pages for missing pages and unexpected server errors.</p>
                <ul>
                    <li><strong>404</strong> - shown when the route does not exist</li>
                    <li><strong>500</strong> - shown when an unexpected server-side error occurs</li>
                </ul>
                <p>These pages show status details and a block of technical information you can send to the app maintainer for support.</p>
                <p>Both error pages also provide direct buttons back to <strong>Home</strong> and <strong>Documentation</strong>.</p>
            </section>

            <section class="box">
                <h2 class="title is-3">Troubleshooting guide</h2>

                <h3 class="title is-5">Problem: I cannot connect to the game server</h3>
                <ol>
                    <li>Open the spawn page and verify the status is <strong>running</strong>.</li>
                    <li>Verify the connection address is exactly <code>{{server_connection_host}}:PORT</code> for your current deployment.</li>
                    <li>Verify you are using the correct spawn port, not just the web panel port.</li>
                    <li>Check the logs and wait for normal startup completion before testing again.</li>
                    <li>If the server was just created, give it time to download and initialize the selected version.</li>
                    <li>If player count is unavailable, the server may still be starting or failing to answer status queries.</li>
                </ol>

                <h3 class="title is-5">Problem: The server status is running but players still cannot join</h3>
                <ol>
                    <li>Check the logs for whitelist, authentication, mod mismatch, or startup errors.</li>
                    <li>Make sure the players are using a compatible client version.</li>
                    <li>For Forge servers, make sure players have the matching mod set.</li>
                    <li>Copy the address from the spawn page instead of typing it manually.</li>
                </ol>

                <h3 class="title is-5">Problem: The server fails to start</h3>
                <ol>
                    <li>Read the latest logs.</li>
                    <li>Use <strong>Analyze</strong> if Gemini is configured.</li>
                    <li>Check for Minecraft version and Forge version mismatch.</li>
                    <li>If mods were recently added, suspect dependency issues or incompatible versions first.</li>
                    <li>If needed, restore a known-good backup.</li>
                    <li>Try <strong>Re-create</strong> after correcting the configuration.</li>
                </ol>

                <h3 class="title is-5">Problem: I uploaded mods and now the server crashes</h3>
                <ol>
                    <li>Check the logs for missing dependencies, duplicate mods, or wrong game version messages.</li>
                    <li>Verify each uploaded mod is a <code>.jar</code> file.</li>
                    <li>Verify the modpack matches the selected Minecraft version and Forge version.</li>
                    <li>Remove the last added mods or restore a backup from before the change.</li>
                </ol>

                <h3 class="title is-5">Problem: I deleted a mod but nothing changed</h3>
                <ol>
                    <li>Check whether the spawn page shows <strong>Pending Del</strong>.</li>
                    <li>Restart or recreate the server so the deletion fully takes effect.</li>
                </ol>

                <h3 class="title is-5">Problem: The logs page says no logs are available</h3>
                <ol>
                    <li>The container may not be created yet.</li>
                    <li>The server may still be starting.</li>
                    <li>The container may have exited before producing useful output.</li>
                    <li>Try <strong>Refresh</strong> or <strong>Re-create</strong>.</li>
                </ol>

                <h3 class="title is-5">Problem: Log analysis does not work</h3>
                <ol>
                    <li>Confirm there are logs to analyze.</li>
                    <li>Confirm <code>GEMINI_API_KEY</code> is configured for the app.</li>
                    <li>Try again after the server has produced enough logs to analyze.</li>
                </ol>

                <h3 class="title is-5">Problem: My server.properties editor is empty</h3>
                <ol>
                    <li>If the server is brand new, let it finish its first startup.</li>
                    <li>Refresh the spawn page afterward.</li>
                    <li>If needed, recreate the server once and check again.</li>
                </ol>

                <h3 class="title is-5">Problem: Restore failed</h3>
                <ol>
                    <li>Check the spawn logs after the restore attempt.</li>
                    <li>If the restored world or mods are incompatible with the configured server type or versions, the server may not start.</li>
                    <li>Use archived backups to restore into a new server if you want to avoid disturbing the current live spawn.</li>
                </ol>

                <h3 class="title is-5">Problem: I deleted a server and want it back</h3>
                <ol>
                    <li>Open <strong>Archived Backups</strong>.</li>
                    <li>Look for the latest archived backup from that server.</li>
                    <li>Restore it into a new spawn.</li>
                    <li>If there is no archived backup, the deleted live files are no longer available through the app.</li>
                </ol>

                <h3 class="title is-5">Problem: I cannot create another server</h3>
                <ol>
                    <li>Check whether the name is already in use.</li>
                    <li>Check whether the port is already in use.</li>
                    <li>Check whether the requested port is outside <code>25565-25665</code>.</li>
                    <li>Check whether all ports in the allowed range have already been assigned.</li>
                    <li>Check whether the version string format is valid.</li>
                </ol>

                <h3 class="title is-5">Problem: I opened a broken link or invalid page</h3>
                <p>The app will show a 404 page with helpful navigation back to <strong>Home</strong> or <strong>Documentation</strong>.</p>

                <h3 class="title is-5">Problem: The app shows an unexpected server error</h3>
                <ol>
                    <li>Open the error page details.</li>
                    <li>Copy the status code and details block.</li>
                    <li>Include the action you were trying to perform.</li>
                    <li>Include the server name if the issue happened on a specific spawn.</li>
                </ol>
            </section>

            <section class="box">
                <h2 class="title is-3">Best practices</h2>
                <ul>
                    <li>Create a manual backup before changing mods, properties, or world-critical settings.</li>
                    <li>After deleting mods, restart or recreate the server before assuming the change is active.</li>
                    <li>Keep Forge, Minecraft, and mod versions aligned.</li>
                    <li>Use archived backups for long-term recovery after deleting old servers.</li>
                    <li>Use the logs first whenever a server behaves unexpectedly.</li>
                </ul>
            </section>
        </div>
    </div>
</section>

%include('./templates/footer.tpl')
