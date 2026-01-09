%include('./templates/header.tpl')

<section class="section">
    <div class="container">
        <h1 class="title is-1">Documentation</h1>
        <p class="subtitle">Learn how to use the Minecraft Server Spawner</p>
        
        <div class="content">
            <!-- Overview -->
            <section class="box">
                <h2 class="title is-3">Overview</h2>
                <p>
                    The Minecraft Server Spawner is a web-based tool that allows you to easily deploy and manage 
                    multiple Minecraft server instances. It supports both vanilla Minecraft and Forge modded servers, 
                    giving you complete control over your server configurations through a simple interface.
                </p>
            </section>

            <!-- Getting Started -->
            <section class="box">
                <h2 class="title is-3">Getting Started</h2>
                <h3 class="title is-4"><i class="fas fa-plus-circle"></i> Creating a New Server</h3>
                <ol>
                    <li>Click the <strong>"Create new spawn"</strong> button on the home page</li>
                    <li>Enter a unique name for your server</li>
                    <li>Specify a port number (each server needs its own port)</li>
                    <li>Select the server type:
                        <ul>
                            <li><strong>Vanilla</strong> - Standard Minecraft server</li>
                            <li><strong>Forge</strong> - Modded Minecraft server</li>
                        </ul>
                    </li>
                    <li>Choose your Minecraft version</li>
                    <li>If using Forge, select your Forge version</li>
                    <li>Click <strong>"Create"</strong> to deploy your server</li>
                </ol>
            </section>

            <!-- Managing Servers -->
            <section class="box">
                <h2 class="title is-3">Managing Servers</h2>
                
                <h3 class="title is-4"><i class="fas fa-play"></i> Starting and Stopping</h3>
                <ul>
                    <li><strong>Start:</strong> Click the <span class="tag is-success">Start</span> button to launch your server</li>
                    <li><strong>Stop:</strong> Click the <span class="tag is-danger">Stop</span> button to gracefully shut down your server</li>
                    <li><strong>Recreate:</strong> Rebuilds the container if configuration changes are needed</li>
                </ul>

                <h3 class="title is-4 mt-5"><i class="fas fa-eye"></i> Viewing Server Status</h3>
                <p>Click on any server from the home page to view its detailed status page, which shows:</p>
                <ul>
                    <li>Current running status (Running, Stopped, etc.)</li>
                    <li>Container information and resource usage</li>
                    <li>Port configuration</li>
                    <li>Server version details</li>
                </ul>

                <h3 class="title is-4 mt-5"><i class="fas fa-file-alt"></i> Viewing Logs</h3>
                <p>Monitor your server's activity by viewing the logs:</p>
                <ul>
                    <li>Navigate to your server's detail page</li>
                    <li>Click the <strong>"View Logs"</strong> button</li>
                    <li>Logs update automatically to show real-time server activity</li>
                </ul>
            </section>

            <!-- Mod Management -->
            <section class="box">
                <h2 class="title is-3">Managing Mods (Forge Only)</h2>
                <p>For Forge servers, you can manage mods directly from the web interface:</p>
                
                <h3 class="title is-4"><i class="fas fa-upload"></i> Adding Mods</h3>
                <ol>
                    <li>Go to your server's detail page</li>
                    <li>Scroll to the <strong>"Mods"</strong> section</li>
                    <li>Click <strong>"Add Mod"</strong></li>
                    <li>Select a .jar mod file from your computer</li>
                    <li>Click <strong>"Upload"</strong></li>
                    <li>Restart your server for changes to take effect</li>
                </ol>

                <h3 class="title is-4 mt-4"><i class="fas fa-exchange-alt"></i> Replacing All Mods</h3>
                <ol>
                    <li>Click <strong>"Replace All Mods"</strong></li>
                    <li>Select multiple .jar files (you can select multiple files at once)</li>
                    <li>This will remove all existing mods and replace them with your selection</li>
                    <li>Restart your server for changes to take effect</li>
                </ol>

                <h3 class="title is-4 mt-4"><i class="fas fa-trash"></i> Removing Mods</h3>
                <ul>
                    <li>Click the delete button next to any mod in the list</li>
                    <li>Restart your server for changes to take effect</li>
                </ul>
            </section>

            <!-- Server Configuration -->
            <section class="box">
                <h2 class="title is-3">Server Configuration</h2>
                <h3 class="title is-4"><i class="fas fa-cog"></i> Server Properties</h3>
                <p>Customize your server settings by editing server.properties:</p>
                <ol>
                    <li>Navigate to your server's detail page</li>
                    <li>Find the <strong>"Server Properties"</strong> section</li>
                    <li>Edit the properties as needed (difficulty, gamemode, max players, etc.)</li>
                    <li>Click <strong>"Save"</strong></li>
                    <li>Restart your server for changes to take effect</li>
                </ol>

                <h3 class="title is-4 mt-5"><i class="fas fa-terminal"></i> Console Commands</h3>
                <p>Send commands directly to your server console:</p>
                <ul>
                    <li>Go to the <strong>"Console"</strong> section on your server's page</li>
                    <li>Type your command (e.g., "op PlayerName", "say Hello")</li>
                    <li>Click <strong>"Send"</strong> to execute</li>
                </ul>
            </section>

            <!-- Backup Management -->
            <section class="box">
                <h2 class="title is-3">Backup Management</h2>
                
                <h3 class="title is-4"><i class="fas fa-save"></i> Creating Backups</h3>
                <ol>
                    <li>Navigate to your server's detail page</li>
                    <li>Find the <strong>"Backups"</strong> section</li>
                    <li>Enter a name for your backup (optional)</li>
                    <li>Click <strong>"Create Backup"</strong></li>
                    <li>The backup will be created in the background</li>
                </ol>

                <h3 class="title is-4 mt-4"><i class="fas fa-undo"></i> Restoring Backups</h3>
                <ol>
                    <li>Navigate to the backups section</li>
                    <li>Find the backup you want to restore</li>
                    <li>Click the <strong>"Restore"</strong> button</li>
                    <li>Your server will be stopped and restored to the backup state</li>
                </ol>

                <h3 class="title is-4 mt-4"><i class="fas fa-clock"></i> Scheduled Backups</h3>
                <p>Configure automatic daily backups:</p>
                <ol>
                    <li>Go to the <strong>"Backup Settings"</strong> section</li>
                    <li>Enable <strong>"Daily Backup"</strong></li>
                    <li>Set the time for automatic backups (hour and minute)</li>
                    <li>Set retention days (how long to keep old backups)</li>
                    <li>Click <strong>"Save Settings"</strong></li>
                </ol>
            </section>

            <!-- Deleting Servers -->
            <section class="box">
                <h2 class="title is-3">Deleting a Server</h2>
                <div class="notification is-warning">
                    <strong>Warning:</strong> Deleting a server will permanently remove all its data, including worlds, configurations, and mods.
                </div>
                <ol>
                    <li>Navigate to the server's detail page</li>
                    <li>Click the <strong>"Delete Server"</strong> button</li>
                    <li>Confirm the deletion</li>
                    <li>All associated data will be permanently removed</li>
                </ol>
            </section>

            <!-- Troubleshooting -->
            <section class="box">
                <h2 class="title is-3">Troubleshooting</h2>
                
                <h3 class="title is-4"><i class="fas fa-exclamation-triangle"></i> Server Won't Start</h3>
                <ul>
                    <li>Check the logs for error messages</li>
                    <li>Ensure the port isn't already in use</li>
                    <li>Verify that the Minecraft and Forge versions are compatible</li>
                    <li>Try recreating the container</li>
                </ul>

                <h3 class="title is-4 mt-4"><i class="fas fa-puzzle-piece"></i> Mods Not Working</h3>
                <ul>
                    <li>Verify mods are compatible with your Forge and Minecraft versions</li>
                    <li>Check for mod conflicts in the logs</li>
                    <li>Ensure the server was restarted after adding/removing mods</li>
                    <li>Make sure all dependencies for the mods are installed</li>
                </ul>

                <h3 class="title is-4 mt-4"><i class="fas fa-network-wired"></i> Can't Connect to Server</h3>
                <ul>
                    <li>Verify the server is running (check status)</li>
                    <li>Ensure you're using the correct port number</li>
                    <li>Check your firewall settings</li>
                    <li>Confirm the server has fully started (check logs for "Done")</li>
                </ul>
            </section>

            <!-- Tips -->
            <section class="box">
                <h2 class="title is-3">Tips & Best Practices</h2>
                <ul>
                    <li><strong>Regular Backups:</strong> Enable automatic daily backups to prevent data loss</li>
                    <li><strong>Port Management:</strong> Keep track of which ports are assigned to which servers</li>
                    <li><strong>Monitor Logs:</strong> Check logs regularly to catch issues early</li>
                    <li><strong>Test Mods:</strong> Test new mods on a separate server before adding to your main server</li>
                    <li><strong>Resource Allocation:</strong> Be mindful of system resources when running multiple servers</li>
                    <li><strong>Version Compatibility:</strong> Always verify mod compatibility with your server versions</li>
                </ul>
            </section>
        </div>
    </div>
</section>

%include('./templates/footer.tpl')
