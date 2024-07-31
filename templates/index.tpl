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

<form method="post" action="/spawn">
    <div class="field m-3">
        <div class="columns">
            <div class="control column">
                <input class="input is-link" type="text" name="name" placeholder="Unique Name (Random UUID)">
            </div>
            <div class="control column">
                <input class="input is-link" type="text" name="port" placeholder="Port (25565)">
            </div>
            <div class="control column">
                <div class="select is-fullwidth">
                    <select name="type">
                        <option>FORGE</option>
                        <option>VANILLA</option>
                    </select>
                </div>
            </div>
            <div class="control column">
                <input class="input is-link" type="text" name="minecraft_version" placeholder="Minecraft Version (LATEST)">
            </div>
            <div class="control column">
                <input class="input is-link" type="text" name="forge_version" placeholder="Forge Version (LATEST)">
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
                <li><a href="/spawn/{{spawn.name}}">{{spawn.name}}</a></li>
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