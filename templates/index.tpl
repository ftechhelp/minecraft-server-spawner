%include('./templates/header.tpl')

<section class="section pt-4 pb-5">
    %if page_error:
    <div class="notification is-danger is-light">
        {{page_error}}
    </div>
    %end
    <div class="is-flex is-justify-content-space-between is-align-items-center mb-4">
        <h1 class="title is-3 mb-0">Servers</h1>
        <button class="button is-link" id="toggleCreateForm">
            <span class="icon"><i class="fa-solid fa-plus"></i></span>
            <span>New Server</span>
        </button>
    </div>

    <div class="modal {{'is-active' if create_error else ''}}" id="createModal">
        <div class="modal-background"></div>
        <div class="modal-card">
            <form method="post" action="/spawn">
                <header class="modal-card-head">
                    <p class="modal-card-title">New Server</p>
                    <button type="button" class="delete create-modal-close" aria-label="close"></button>
                </header>
                <section class="modal-card-body">
                    %if create_error:
                    <div class="notification is-danger is-light">
                        {{create_error}}
                    </div>
                    %end
                    <div class="field">
                        <label class="label">Name</label>
                        <div class="control">
                            <input class="input is-link" type="text" name="name" placeholder="Unique Name (Random UUID)" value="{{create_form.get('name', '')}}">
                        </div>
                    </div>
                    <div class="field">
                        <label class="label">Port</label>
                        <div class="control">
                            <input class="input is-link" type="number" name="port" placeholder="Port (25565-25665)" min="25565" max="25665" value="{{create_form.get('port', '')}}">
                        </div>
                    </div>
                    <div class="field">
                        <label class="label">Type</label>
                        <div class="control">
                            <div class="select is-fullwidth">
                                <select name="type">
                                    <option {{'selected' if create_form.get('type', 'FORGE') == 'FORGE' else ''}}>FORGE</option>
                                    <option {{'selected' if create_form.get('type', 'FORGE') == 'NEOFORGE' else ''}}>NEOFORGE</option>
                                    <option {{'selected' if create_form.get('type', 'FORGE') == 'VANILLA' else ''}}>VANILLA</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="field">
                        <label class="label">Minecraft Version</label>
                        <div class="control">
                            <input class="input is-link" type="text" name="minecraft_version" placeholder="Minecraft Version (LATEST)" value="{{create_form.get('minecraft_version', '')}}">
                        </div>
                    </div>
                    <div class="field">
                        <label class="label">Forge/NeoForge Version</label>
                        <div class="control">
                            <input class="input is-link" type="text" name="forge_version" placeholder="Forge/NeoForge Version (LATEST)" value="{{create_form.get('forge_version', '')}}">
                        </div>
                    </div>
                </section>
                <footer class="modal-card-foot">
                    <button type="submit" class="button is-link" id="spawnButton">
                        Spawn
                    </button>
                    <button type="button" class="button create-modal-close">Cancel</button>
                </footer>
            </form>
        </div>
    </div>

    %running_count = sum(1 for s in spawns.values() if s.get_status() == 'running')
    <nav class="level box">
        <div class="level-item has-text-centered">
            <div>
                <p class="heading">Servers</p>
                <p class="title">{{len(spawns)}}</p>
            </div>
        </div>
        <div class="level-item has-text-centered">
            <div>
                <p class="heading">Running</p>
                <p class="title" id="statRunning">{{running_count}}</p>
            </div>
        </div>
        <div class="level-item has-text-centered">
            <div>
                <p class="heading">Players Online</p>
                <p class="title" id="statPlayers">&mdash;</p>
            </div>
        </div>
        <div class="level-item has-text-centered">
            <div>
                <p class="heading">Eggs In Use</p>
                <p class="title">{{eggs_used}}/{{eggs_total}}</p>
            </div>
        </div>
    </nav>

    %if not spawns:
    <div class="notification is-light has-text-centered">
        No servers yet. Click <strong>+ New Server</strong> above to spawn your first one.
    </div>
    %end

    <div class="columns is-multiline">
        %for spawn in spawns.values():
            %status = spawn.get_status()
            %if status == 'running':
                %status_class = 'is-success'
            %elif status in ['created', 'restarting', 'removing', 'paused', 'exited']:
                %status_class = 'is-warning'
            %else:
                %status_class = 'is-danger'
            %end
        <div class="column is-one-third-desktop is-half-tablet">
            <div class="card spawn-card" data-spawn="{{spawn.name}}">
                <div class="card-content pb-3">
                    <div class="is-flex is-justify-content-space-between is-align-items-center mb-3">
                        <a class="title is-5 mb-0" href="/spawn/{{spawn.name}}">{{spawn.name}}</a>
                        <span class="tag spawn-status {{status_class}}">{{status}}</span>
                    </div>
                    <div class="tags mb-2">
                        <span class="tag is-dark">{{spawn.type}}</span>
                        <span class="tag is-light">MC {{spawn.minecraft_version}}</span>
                        %if spawn.type in ('FORGE', 'NEOFORGE'):
                        <span class="tag is-light">{{spawn.type.title()}} {{spawn.forge_version}}</span>
                        %end
                        <span class="tag is-light">Port {{spawn.port}}</span>
                        <span class="tag {{'is-info is-light' if spawn.owner else 'is-light'}}">
                            {{spawn.owner if spawn.owner else 'unowned'}}
                        </span>
                    </div>
                    <p>
                        <span class="icon is-small has-text-grey"><i class="fa-solid fa-users"></i></span>
                        <span class="spawn-players">&mdash;</span> players
                    </p>
                </div>
                <footer class="card-footer">
                    <a class="card-footer-item" href="/spawn/{{spawn.name}}">Manage</a>
                    %if can_manage.get(spawn.name):
                        %if status == 'running':
                    <form class="card-footer-item quick-action" action="/spawn/{{spawn.name}}/stop" method="post" data-action="stopping">
                        <input type="hidden" name="redirect" value="/">
                        <button type="submit" class="button is-warning is-small">Stop</button>
                    </form>
                        %else:
                    <form class="card-footer-item quick-action" action="/spawn/{{spawn.name}}/start" method="post" data-action="starting">
                        <input type="hidden" name="redirect" value="/">
                        <button type="submit" class="button is-success is-small">Start</button>
                    </form>
                        %end
                    %end
                </footer>
            </div>
        </div>
        %end
    </div>
</section>

<script type="text/javascript">
    const WARNING_STATUSES = ['created', 'restarting', 'removing', 'paused', 'exited'];
    const spawnStatuses = {};

    function statusTagClass(status) {
        if (status === 'running') return 'is-success';
        if (WARNING_STATUSES.includes(status)) return 'is-warning';
        return 'is-danger';
    }

    function updateStats() {
        let running = 0;
        let players = 0;
        Object.values(spawnStatuses).forEach((data) => {
            if (data.status === 'running') running++;
            if (typeof data.player_count === 'number') players += data.player_count;
        });
        $('#statRunning').text(running);
        $('#statPlayers').text(players);
    }

    function refreshSpawnCard(card) {
        const name = card.dataset.spawn;
        return fetch(`/spawn/${name}/status`)
            .then((response) => response.json())
            .then((data) => {
                spawnStatuses[name] = data;
                const tag = card.querySelector('.spawn-status');
                tag.textContent = data.status || 'N/A';
                tag.className = 'tag spawn-status ' + statusTagClass(data.status);
                const players = card.querySelector('.spawn-players');
                if (data.status === 'running' && typeof data.player_count === 'number') {
                    players.textContent = `${data.player_count} / ${data.player_capacity ?? '?'}`;
                } else {
                    players.textContent = '—';
                }
            })
            .catch(() => {});
    }

    function refreshAllSpawns() {
        const cards = Array.from(document.querySelectorAll('.spawn-card'));
        Promise.all(cards.map(refreshSpawnCard)).then(updateStats);
    }

    $(document).ready(function() {
        $('#toggleCreateForm').click(() => {
            $('#createModal').addClass('is-active');
        });

        $('#createModal .create-modal-close, #createModal .modal-background').on('click', () => {
            $('#createModal').removeClass('is-active');
        });

        $(document).on('keydown', (event) => {
            if (event.key === 'Escape') {
                $('#createModal').removeClass('is-active');
            }
        });

        $('#createModal form').on('submit', () => {
            $('#createModal').removeClass('is-active');
            showLoadingModal('Server is spawning. Please wait...');
        });

        $('.quick-action').on('submit', function() {
            showLoadingModal(`Server is ${$(this).data('action')}. Please wait...`);
        });

        refreshAllSpawns();
        setInterval(refreshAllSpawns, 10000);
    });
</script>

%include('./templates/footer.tpl')
