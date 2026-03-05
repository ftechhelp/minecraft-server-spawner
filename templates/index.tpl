%include('./templates/header.tpl')

<script type="text/javascript">
    $(document).ready(function() 
    {
        $('#spawnButton').click(() => 
        {
            $('#actionModalText').text('Server is spawning. Please Wait...');
            $('#actionModal').toggleClass('is-active');
        });
    });
</script>

%if create_error:
<div class="notification is-danger is-light m-3">
    {{create_error}}
</div>
%end

<form method="post" action="/spawn">
    <div class="field m-3">
        <div class="columns">
            <div class="control column">
                <input class="input is-link" type="text" name="name" placeholder="Unique Name (Random UUID)" value="{{create_form.get('name', '')}}">
            </div>
            <div class="control column">
                <input class="input is-link" type="number" name="port" placeholder="Port (25565-25665)" min="25565" max="25665" value="{{create_form.get('port', '')}}">
            </div>
            <div class="control column">
                <div class="select is-fullwidth">
                    <select name="type">
                        <option {{'selected' if create_form.get('type', 'FORGE') == 'FORGE' else ''}}>FORGE</option>
                        <option {{'selected' if create_form.get('type', 'FORGE') == 'VANILLA' else ''}}>VANILLA</option>
                    </select>
                </div>
            </div>
            <div class="control column">
                <input class="input is-link" type="text" name="minecraft_version" placeholder="Minecraft Version (LATEST)" value="{{create_form.get('minecraft_version', '')}}">
            </div>
            <div class="control column">
                <input class="input is-link" type="text" name="forge_version" placeholder="Forge Version (LATEST)" value="{{create_form.get('forge_version', '')}}">
            </div>
            <p class="control column">
                <button type="submit" class="button is-link is-fullwidth" id="spawnButton">
                    Spawn
                </button>
            </p>
        </div>
    </div>
</form>

<div class="columns">
    <div class="column is-3">
        <aside class="menu m-3">
            <p class="menu-label">Spawns</p>
            <ul class="menu-list">
                %for spawn in spawns.values():
                    %if spawn.get_status() == "running":
                    <li> 
                        <a class="columns" href="/spawn/{{spawn.name}}">
                            <span class="pr-2">{{spawn.name}}</span> <p class="has-text-success">({{spawn.get_status()}})</p>
                        </a>
                    </li>
                    %elif spawn.get_status() in ["created", "restarting", "removing", "paused", "exited"]:
                    <li>
                        <a class="columns" href="/spawn/{{spawn.name}}">
                            <span class="pr-2">{{spawn.name}}</span>
                            <p class="has-text-warning">({{spawn.get_status()}})</p>
                        </a>
                    </li>
                    %else:
                    <li>
                        <a class="columns" href="/spawn/{{spawn.name}}">
                            <span class="pr-2">{{spawn.name}}</span>
                            <p class="has-text-danger">({{spawn.get_status()}})</p>
                        </a>
                    </li>
                    %end
                %end
            </ul>
        </aside>
    </div>
    <div class="column is-6">
    <h1>Some overall spawn stats</h1>
    </div>
    <div class="column is-3">
    
    </div>
</div>

%include('./templates/footer.tpl')