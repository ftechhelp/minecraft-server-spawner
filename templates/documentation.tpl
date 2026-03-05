%include('./templates/header.tpl')

<section class="section">
    <div class="container">
        <h1 class="title is-1">Documentation</h1>
        <p class="subtitle">Complete guide for creating, connecting to, and managing Minecraft servers</p>

        <div class="notification is-info is-light">
            <p><strong>Host:</strong> This panel is hosted on <strong>minecraft.vfontaine.ca</strong>.</p>
            <p><strong>Minecraft connection format:</strong> <code>vfontaine.ca:PORT</code> (example: <code>vfontaine.ca:25565</code>).</p>
        </div>

        <div class="content">
            <section class="box">
                <h2 class="title is-3">Quick Start (First 5 Minutes)</h2>
                <ol>
                    <li>Open <strong>Home</strong> and create a server.</li>
                    <li>Choose a unique name (or leave name blank to auto-generate one).</li>
                    <li>Choose a port (or leave blank to auto-pick the next available port).</li>
                    <li>Pick server type (<strong>FORGE</strong> or <strong>VANILLA</strong>) and versions.</li>
                    <li>Wait until status is <strong>running</strong> and logs contain <code>Done</code>.</li>
                    <li>Connect from Minecraft using <code>vfontaine.ca:PORT</code>.</li>
                    <li>Use <strong>Archived Backups</strong> in the navbar to manage backups preserved after spawn deletion.</li>
                </ol>
            </section>

            <section class="box">
                <h2 class="title is-3">Connection Instructions</h2>
                <h3 class="title is-5"><i class="fas fa-plug"></i> Java Edition</h3>
                <ol>
                    <li>Open Minecraft Java Edition.</li>
                    <li>Go to <strong>Multiplayer</strong> → <strong>Add Server</strong>.</li>
                    <li>For <strong>Server Address</strong>, enter: <code>vfontaine.ca:PORT</code>.</li>
                    <li>Use the exact port shown on the server card/details page.</li>
                </ol>

                <table class="table is-fullwidth is-striped">
                    <thead>
                        <tr>
                            <th>Server Name</th>
                            <th>Port</th>
                            <th>Address to Share</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>survival-main</td>
                            <td>25565</td>
                            <td><code>vfontaine.ca:25565</code></td>
                        </tr>
                        <tr>
                            <td>modded-rpg</td>
                            <td>25570</td>
                            <td><code>vfontaine.ca:25570</code></td>
                        </tr>
                    </tbody>
                </table>

                <div class="notification is-warning is-light">
                    <strong>Important:</strong> If someone can reach the web panel but not the game server, confirm they are using the correct <strong>port</strong> and that the server status is <strong>running</strong>.
                </div>
            </section>

            <section class="box">
                <h2 class="title is-3">Creating Servers (Robust Validation Rules)</h2>
                <p>The create flow includes safety checks to prevent common multi-server mistakes:</p>
                <ul>
                    <li>Spawn name must be valid (letters/numbers/hyphen/underscore, no path characters).</li>
                    <li>Duplicate server names are blocked.</li>
                    <li>Duplicate server directories are blocked.</li>
                    <li>Ports are limited to <code>25565-25665</code>.</li>
                    <li>Duplicate ports are blocked.</li>
                    <li>If port is blank, the app chooses the next free port automatically.</li>
                    <li>Server type is restricted to <strong>FORGE</strong> or <strong>VANILLA</strong>.</li>
                    <li>Minecraft and Forge versions are format-validated.</li>
                </ul>
            </section>

            <section class="box">
                <h2 class="title is-3">Server Operations</h2>
                <div class="columns is-multiline">
                    <div class="column is-6">
                        <h3 class="title is-5"><i class="fas fa-play"></i> Start</h3>
                        <p>Starts a stopped server container.</p>
                    </div>
                    <div class="column is-6">
                        <h3 class="title is-5"><i class="fas fa-stop"></i> Stop</h3>
                        <p>Stops server cleanly. Use this before sensitive file operations.</p>
                    </div>
                    <div class="column is-6">
                        <h3 class="title is-5"><i class="fas fa-sync"></i> Recreate</h3>
                        <p>Rebuilds/recreates the container with current config.</p>
                    </div>
                    <div class="column is-6">
                        <h3 class="title is-5"><i class="fas fa-file-alt"></i> Logs</h3>
                        <p>Check logs for startup success, mod errors, and crash diagnostics.</p>
                    </div>
                </div>
            </section>

            <section class="box">
                <h2 class="title is-3">Forge Mods Workflow</h2>
                <ol>
                    <li>Open a FORGE server page.</li>
                    <li>Upload one mod or replace all mods with a selected set of <code>.jar</code> files.</li>
                    <li>Restart/recreate the server.</li>
                    <li>Watch logs for dependency/conflict errors.</li>
                </ol>
                <p><strong>Tip:</strong> Keep modpack + Forge + Minecraft versions aligned before inviting players.</p>
            </section>

            <section class="box">
                <h2 class="title is-3">Backups and Recovery</h2>
                <ul>
                    <li>Create manual backups before changing mods or properties.</li>
                    <li>Enable daily backups and set retention days to control storage.</li>
                    <li>Restore a backup if a world/mod update causes instability.</li>
                    <li>When deleting a spawn, the latest backup is copied to the root <code>backups</code> archive folder before deletion.</li>
                </ul>
                <h3 class="title is-5 mt-4">Archived Backups Page</h3>
                <p>Open <strong>Archived Backups</strong> from the navbar (<code>/backups</code>) to manage preserved backups.</p>
                <ul>
                    <li>See where a backup came from (source server name).</li>
                    <li>See server type and Minecraft/Forge version metadata.</li>
                    <li>Restore an archived backup into a <strong>new server</strong> (new name + next available port).</li>
                    <li>Permanently delete archived backups (with confirmation popup).</li>
                </ul>

                <div class="notification is-warning is-light">
                    <strong>Important:</strong> Deleting a spawn still removes that spawn's live files. The archived backup is your preserved restore point.
                </div>

                <div class="notification is-danger is-light">
                    <strong>Archived backup delete is permanent:</strong> once removed from <code>/backups</code>, it cannot be recovered.
                </div>
            </section>

            <section class="box">
                <h2 class="title is-3">Troubleshooting</h2>
                <h3 class="title is-5">Issue: "I cannot connect"</h3>
                <ol>
                    <li>Confirm server status is <strong>running</strong>.</li>
                    <li>Confirm logs show startup complete (<code>Done</code>).</li>
                    <li>Confirm address format is exactly <code>vfontaine.ca:PORT</code>.</li>
                    <li>Confirm you used the correct spawn port.</li>
                </ol>

                <h3 class="title is-5 mt-4">Issue: "Server fails to start"</h3>
                <ul>
                    <li>Check logs for version mismatch or mod dependency errors.</li>
                    <li>Verify Minecraft/Forge version compatibility.</li>
                    <li>Try recreate after fixing configuration.</li>
                </ul>
            </section>
        </div>
    </div>
</section>

%include('./templates/footer.tpl')
