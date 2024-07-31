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
    </div>
    <div class="column is-8">
        <article class="message">
            <div class="message-header">
                <p class="subtitle is-4">Log</p>
                <form action="/spawn/{{spawn.name}}/refresh" method="post">
                    <button id="refreshLogButton" class="button is-link">Refresh</button>
                </form>
            </div>
            <div class="message-body">
                <pre>{{spawn.logs}}</pre>
            </div>
        </article>
    </div>
</div>

%include('./templates/footer.tpl')