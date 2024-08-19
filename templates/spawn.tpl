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
            $('#actionModalText').text('Server is deleting. Please Wait...');
            $('#actionModal').toggleClass('is-active');
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
                                    <h4 class="subtitle is-4">{{len(spawn.mods)}}</h4>
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    <h4 class="subtitle is-4">Pending Mods to Remove:</h4>
                                </td>
                                <td>
                                    %if len(spawn.unloadedRemovedMods) > 0:
                                        <h4 class="subtitle is-4 has-text-warning">{{len(spawn.unloadedRemovedMods)}}</h4>
                                    %else:
                                        <h4 class="subtitle is-4">{{len(spawn.unloadedRemovedMods)}}</h4>
                                    %end
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    <h4 class="subtitle is-4">Pending Mods to Add:</h4>
                                </td>
                                <td>
                                    %if len(spawn.unloadedAddedMods) > 0:
                                        <h4 class="subtitle is-4 has-text-warning">{{len(spawn.unloadedAddedMods)}}</h4>
                                    %else:
                                        <h4 class="subtitle is-4">{{len(spawn.unloadedAddedMods)}}</h4>
                                    %end
                                </td>
                            </tr>
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
                <form class="card-footer-item" action="/spawn/{{spawn.name}}/delete" method="post">
                    <button id="deleteButton" class="">Delete</button>
                </form>
            </footer>
        </div>
        <label class="label">Mods</label>
        %for mod in spawn.virtualMods:
        <form action="/spawn/{{spawn.name}}/mods/delete" method="post">
            <div class="field has-addons p-1">
                <div class="control is-expanded">
                    <input class="input" type="text" name="mod" placeholder="Link to mod" value="{{mod}}" readonly>
                </div>
                <div class="control">
                    <button class="button is-danger">
                        Remove
                    </button>
                </div>
            </div>
        </form>
        %end
        <form action="/spawn/{{spawn.name}}/mods/add" method="post">
            <div class="field has-addons p-1">
                <div class="control is-expanded">
                    <input class="input" type="text" name="mod" placeholder="Link to mod" value="">
                </div>
                <div class="control">
                    <button class="button is-info">
                        Add
                    </button>
                </div>
            </div>
        </form>
        <form action="/spawn/{{spawn.name}}/mods/sync" method="post">
            <div class="field has-addons p-1">
                <div class="control is-expanded">
                    <button class="button is-primary" id="modsSyncButton">
                        Sync
                    </button>
                </div>
            </div>
        </form>
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

%include('./templates/footer.tpl')