%include('./templates/header.tpl')

<script type="text/javascript">
    $(document).ready(function () 
    {
        const connectionAddress = '{{server_connection_host}}:{{spawn.port}}';

        $('#recreateButton').click(() => 
        {
            showLoadingModal('Server is re-creating. Please wait...');
        });

        $('#copyAddressButton').click(async () => {
            const $button = $('#copyAddressButton');
            const originalLabel = $button.html();

            try {
                if (navigator.clipboard && window.isSecureContext) {
                    await navigator.clipboard.writeText(connectionAddress);
                } else {
                    const textArea = document.createElement('textarea');
                    textArea.value = connectionAddress;
                    textArea.style.position = 'fixed';
                    textArea.style.opacity = '0';
                    document.body.appendChild(textArea);
                    textArea.focus();
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                }

                $button.removeClass('is-link').addClass('is-success');
                $button.html('<span class="icon"><i class="fas fa-check"></i></span><span>Copied</span>');
                setTimeout(() => {
                    $button.removeClass('is-success').addClass('is-link');
                    $button.html(originalLabel);
                }, 1800);
            } catch (err) {
                console.error('Failed to copy server address:', err);
                $button.removeClass('is-link').addClass('is-danger');
                $button.html('<span class="icon"><i class="fas fa-times"></i></span><span>Copy failed</span>');
                setTimeout(() => {
                    $button.removeClass('is-danger').addClass('is-link');
                    $button.html(originalLabel);
                }, 2200);
            }
        });

        $('#startButton').click(() => 
        {
            showLoadingModal('Server is starting. Please wait...');
        });

        $('#stopButton').click(() => 
        {
            showLoadingModal('Server is stopping. Please wait...');
        });

        $('#deleteButton').click(() => {
            $('#deleteConfirmModal').toggleClass('is-active');
            return false;
        });

        $('#confirmDeleteButton').click(() => {
            $('#deleteConfirmModal').toggleClass('is-active');
            showLoadingModal('Server is deleting. Please wait...');
            $('#deleteForm').submit();
        });

        $('#cancelDeleteButton').click(() => {
            $('#deleteConfirmModal').removeClass('is-active');
        });
        $(document).on('click', '.cancel-delete-btn', function() {
            $('#deleteConfirmModal').removeClass('is-active');
        });
        $('#deleteAllModsButton').click(() => {
            $('#deleteAllModsConfirmModal').addClass('is-active');
            return false;
        });

        $('#confirmDeleteAllModsButton').click(() => {
            $('#deleteAllModsConfirmModal').removeClass('is-active');
            showLoadingModal('Deleting all mods. Please wait...');
            $('#deleteAllModsForm').submit();
        });

        $('#cancelDeleteAllModsButton').click(() => {
            $('#deleteAllModsConfirmModal').removeClass('is-active');
        });

        $(document).on('click', '#deleteAllModsConfirmModal .modal-background, #deleteAllModsConfirmModal .delete', function() {
            $('#deleteAllModsConfirmModal').removeClass('is-active');
        });
        const LOG_REFRESH_INTERVAL_MS = 5000;
        let streamTimer = null;
        let isStreaming = false;
        let logRequestInFlight = false;

        // Scroll logs to bottom on load
        function scrollLogsToBottom() {
            const logsContainer = $('#logsContainer');
            if (logsContainer.length) {
                logsContainer.scrollTop(logsContainer[0].scrollHeight);
            }
        }

        // Fetch and update logs
        function refreshLogs() {
            if (logRequestInFlight) {
                return $.Deferred().resolve().promise();
            }

            logRequestInFlight = true;
            return $.get(window.location.pathname + '/logs/content')
                .done(function(data) {
                    $('#logsContent').text(data);
                    scrollLogsToBottom();
                })
                .fail(function() {
                    console.error('Failed to fetch logs');
                })
                .always(function() {
                    logRequestInFlight = false;
                });
        }

        function scheduleNextLogRefresh() {
            if (!isStreaming) {
                return;
            }

            streamTimer = window.setTimeout(function() {
                refreshLogs().always(scheduleNextLogRefresh);
            }, LOG_REFRESH_INTERVAL_MS);
        }

        function startLogStreaming() {
            isStreaming = true;
            const $streamButton = $('#streamButton');
            $streamButton.removeClass('is-outlined is-info').addClass('is-success');
            $streamButton.html('<span class="icon"><i class="fas fa-broadcast-tower"></i></span><span>Streaming</span>');
            refreshLogs().always(scheduleNextLogRefresh);
        }

        function stopLogStreaming() {
            isStreaming = false;
            const $streamButton = $('#streamButton');
            $streamButton.removeClass('is-success').addClass('is-outlined is-info');
            $streamButton.html('<span class="icon"><i class="fas fa-broadcast-tower"></i></span><span>Stream</span>');
            if (streamTimer) {
                clearTimeout(streamTimer);
                streamTimer = null;
            }
        }

        function openAnalysisModal(title, bodyHtml, articleClass = 'is-info') {
            $('#logAnalysisModalTitle').text(title);
            $('#logAnalysisMessage').removeClass('is-info is-success is-warning is-danger').addClass(articleClass);
            $('#logAnalysisBody').html(bodyHtml);
            $('#logAnalysisModal').addClass('is-active');
        }

        function closeAnalysisModal() {
            $('#logAnalysisModal').removeClass('is-active');
        }

        function escapeHtml(value) {
            return $('<div>').text(value || '').html();
        }

        function formatBytes(bytes) {
            const value = Number(bytes) || 0;
            if (value <= 0) {
                return '0 B';
            }

            const units = ['B', 'KB', 'MB', 'GB', 'TB'];
            const exponent = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
            const amount = value / Math.pow(1024, exponent);
            const precision = exponent === 0 ? 0 : 1;
            return `${amount.toFixed(precision)} ${units[exponent]}`;
        }

        function formatDuration(seconds) {
            if (!isFinite(seconds) || seconds < 0) {
                return 'Calculating...';
            }

            if (seconds < 60) {
                return `${Math.max(1, Math.round(seconds))} sec`;
            }

            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = Math.round(seconds % 60);
            return `${minutes} min ${remainingSeconds} sec`;
        }

        function resetBulkUploadProgress() {
            $('#bulkUploadProgressWrapper').addClass('is-hidden');
            $('#bulkUploadProgressBar').val(0);
            $('#bulkUploadProgressPercent').text('0%');
            $('#bulkUploadProgressTransferred').text('0 B / 0 B');
            $('#bulkUploadProgressSpeed').text('0 B/s');
            $('#bulkUploadProgressEta').text('Waiting...');
            $('#bulkUploadProgressStatus').text('Preparing upload...');
        }

        function showBulkUploadProgress() {
            $('#bulkUploadProgressWrapper').removeClass('is-hidden');
        }

        function setBulkUploadProcessingState() {
            $('#bulkUploadProgressBar').val(100);
            $('#bulkUploadProgressPercent').text('100%');
            $('#bulkUploadProgressEta').text('Processing...');
            $('#bulkUploadProgressStatus').text('Upload complete. Applying mods and restarting server...');
        }

        function requestJson(url, method = 'POST', body = null) {
            return fetch(url, {
                method,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                },
                body
            }).then(async (response) => {
                let payload = {};

                try {
                    payload = await response.json();
                } catch (error) {
                    console.error('Failed to parse JSON response', error);
                }

                if (!response.ok || !payload.ok) {
                    throw new Error(payload.error || 'Request failed.');
                }

                return payload;
            });
        }

        function uploadBulkBatchFile(url, batchId, file, uploadedBytesBeforeFile, totalBytes, fileIndex, totalFiles, startTime) {
            return new Promise((resolve, reject) => {
                const formData = new FormData();
                formData.append('batch_id', batchId);
                formData.append('mod', file, file.name);

                const xhr = new XMLHttpRequest();
                xhr.open('POST', url, true);
                xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
                xhr.setRequestHeader('Accept', 'application/json');

                xhr.upload.addEventListener('progress', function(progressEvent) {
                    if (!progressEvent.lengthComputable) {
                        return;
                    }

                    const totalLoaded = uploadedBytesBeforeFile + progressEvent.loaded;
                    const percent = totalBytes > 0 ? Math.min(100, Math.round((totalLoaded / totalBytes) * 100)) : 0;
                    const elapsedSeconds = Math.max((Date.now() - startTime) / 1000, 0.1);
                    const bytesPerSecond = totalLoaded / elapsedSeconds;
                    const remainingBytes = Math.max(totalBytes - totalLoaded, 0);
                    const etaSeconds = bytesPerSecond > 0 ? remainingBytes / bytesPerSecond : Infinity;

                    $('#bulkUploadProgressBar').val(percent);
                    $('#bulkUploadProgressPercent').text(`${percent}%`);
                    $('#bulkUploadProgressTransferred').text(`${formatBytes(totalLoaded)} / ${formatBytes(totalBytes)}`);
                    $('#bulkUploadProgressSpeed').text(`${formatBytes(bytesPerSecond)}/s`);
                    $('#bulkUploadProgressEta').text(formatDuration(etaSeconds));
                    $('#bulkUploadProgressStatus').text(`Uploading mod ${fileIndex} of ${totalFiles}...`);
                });

                xhr.addEventListener('load', function() {
                    let payload = {};

                    try {
                        payload = xhr.responseText ? JSON.parse(xhr.responseText) : {};
                    } catch (error) {
                        console.error('Failed to parse staged bulk upload response', error);
                    }

                    if (xhr.status >= 200 && xhr.status < 300 && payload.ok) {
                        resolve();
                        return;
                    }

                    reject(new Error(payload.error || `Failed while uploading ${file.name}.`));
                });

                xhr.addEventListener('error', function() {
                    reject(new Error(`Network error while uploading ${file.name}.`));
                });

                xhr.addEventListener('abort', function() {
                    reject(new Error(`Upload was cancelled while sending ${file.name}.`));
                });

                xhr.send(formData);
            });
        }

        function resetSingleUploadProgress() {
            $('#singleUploadProgressWrapper').addClass('is-hidden');
            $('#singleUploadProgressBar').val(0);
            $('#singleUploadProgressPercent').text('0%');
            $('#singleUploadProgressTransferred').text('0 B / 0 B');
            $('#singleUploadProgressSpeed').text('0 B/s');
            $('#singleUploadProgressEta').text('Waiting...');
            $('#singleUploadProgressStatus').text('Preparing upload...');
        }

        function showSingleUploadProgress() {
            $('#singleUploadProgressWrapper').removeClass('is-hidden');
        }

        function setSingleUploadProcessingState() {
            $('#singleUploadProgressBar').val(100);
            $('#singleUploadProgressPercent').text('100%');
            $('#singleUploadProgressEta').text('Processing...');
            $('#singleUploadProgressStatus').text('Upload complete. Applying mod and restarting server...');
        }

        function renderStatus(status) {
            let tagClass = 'is-success';
            if (status === 'running') {
                tagClass = 'is-success';
            } else if (['created', 'restarting', 'removing', 'paused', 'exited'].includes(status)) {
                tagClass = 'is-warning';
            } else {
                tagClass = 'is-danger';
            }

            $('#spawnStatusValue').html(`<span class="tag ${tagClass}">${escapeHtml(status || 'N/A')}</span>`);
        }

        function renderPlayerCount(playerCount, playerCapacity) {
            const $playerCountValue = $('#playerCountValue');

            if (playerCount === '') {
                playerCount = null;
            }

            if (playerCapacity === '') {
                playerCapacity = null;
            }

            if (playerCount !== null && playerCount !== undefined && playerCapacity !== null && playerCapacity !== undefined) {
                $playerCountValue.html(`<span class="tag is-info">${escapeHtml(String(playerCount))} / ${escapeHtml(String(playerCapacity))}</span>`);
                return;
            }

            if (playerCount !== null && playerCount !== undefined) {
                $playerCountValue.html(`<span class="tag is-info">${escapeHtml(String(playerCount))}</span>`);
                return;
            }

            $playerCountValue.html('<span class="has-text-grey">Unavailable</span>');
        }

        function renderAnalysisResult(analysis) {
            const summary = escapeHtml(analysis.summary || 'Analysis complete.');

            if (analysis.outcome === 'normal') {
                openAnalysisModal(
                    'Log Analysis',
                    `<p>${summary}</p>`,
                    'is-success'
                );
                return;
            }

            const problem = escapeHtml(analysis.problem || 'Problem detected');
            const details = escapeHtml(analysis.details || 'The logs suggest a likely issue.');
            openAnalysisModal(
                'Log Analysis',
                `<p><strong>Summary:</strong> ${summary}</p><p class="mt-3"><strong>Problem:</strong> ${problem}</p><p class="mt-3"><strong>Details:</strong> ${details}</p>`,
                'is-warning'
            );
        }

        $('#analyzeLogsButton').click(function() {
            const $button = $(this);
            const originalHtml = $button.html();

            $button.addClass('is-loading').prop('disabled', true);
            $button.html('<span class="icon"><i class="fas fa-wand-magic-sparkles"></i></span><span>Analyzing</span>');

            $.ajax({
                url: window.location.pathname + '/logs/analyze',
                method: 'POST',
                dataType: 'json'
            }).done(function(response) {
                if (!response.ok) {
                    openAnalysisModal('Log Analysis', `<p>${escapeHtml(response.error || 'Analysis failed.')}</p>`, 'is-danger');
                    return;
                }

                renderAnalysisResult(response.analysis || {});
            }).fail(function(xhr) {
                let errorMessage = 'Analysis failed.';

                try {
                    const payload = JSON.parse(xhr.responseText);
                    errorMessage = payload.error || errorMessage;
                } catch (e) {
                    console.error('Failed to parse analysis error response', e);
                }

                openAnalysisModal('Log Analysis', `<p>${escapeHtml(errorMessage)}</p>`, 'is-danger');
            }).always(function() {
                $button.removeClass('is-loading').prop('disabled', false);
                $button.html(originalHtml);
            });
        });

        // Toggle streaming
        function toggleStreaming() {
            if (isStreaming) {
                stopLogStreaming();
            } else {
                startLogStreaming();
            }
        }

        $('#streamButton').click(toggleStreaming);

        $('#refreshLogButton').click(() => {
            $('#refreshLogButton').addClass('is-loading');
            refreshLogs().always(() => $('#refreshLogButton').removeClass('is-loading'));
        });

        $('#closeLogAnalysisModal, #dismissLogAnalysisModal').click(closeAnalysisModal);
        $('#logAnalysisModal .modal-background, #logAnalysisModal .delete').click(closeAnalysisModal);

        // Scroll to bottom on initial load
        scrollLogsToBottom();

        // Streaming is opt-in. It is intentionally not started on page load:
        // logs can be large and must not make the rest of the panel sluggish.
        window.addEventListener('beforeunload', stopLogStreaming);

        $('#modsSyncButton').click(() => 
        {
            showLoadingModal('Mods are synching and server is restarting. Please wait...');
        });
        
        $('#updateServerPropertiesButton').click(() => 
        {
            showLoadingModal('Properties are updating and server is restarting. Please wait...');
        });

        $('#addModForm').on('submit', function(event) {
            event.preventDefault();

            const formElement = this;
            const $form = $(formElement);
            const $submitButton = $('#addModButton');
            const fileInput = formElement.querySelector('input[name="mod"]');
            let uploadTransferComplete = false;

            if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
                return;
            }

            const formData = new FormData(formElement);
            const startTime = Date.now();

            showSingleUploadProgress();
            $('#singleUploadProgressStatus').text('Uploading mod...');
            $submitButton.prop('disabled', true).addClass('is-loading');

            const xhr = new XMLHttpRequest();
            xhr.open('POST', $form.attr('action'), true);
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            xhr.setRequestHeader('Accept', 'application/json');

            xhr.upload.addEventListener('progress', function(progressEvent) {
                if (!progressEvent.lengthComputable) {
                    return;
                }

                const loaded = progressEvent.loaded;
                const total = progressEvent.total;
                const percent = total > 0 ? Math.min(100, Math.round((loaded / total) * 100)) : 0;
                const elapsedSeconds = Math.max((Date.now() - startTime) / 1000, 0.1);
                const bytesPerSecond = loaded / elapsedSeconds;
                const remainingBytes = Math.max(total - loaded, 0);
                const etaSeconds = bytesPerSecond > 0 ? remainingBytes / bytesPerSecond : Infinity;

                $('#singleUploadProgressBar').val(percent);
                $('#singleUploadProgressPercent').text(`${percent}%`);
                $('#singleUploadProgressTransferred').text(`${formatBytes(loaded)} / ${formatBytes(total)}`);
                $('#singleUploadProgressSpeed').text(`${formatBytes(bytesPerSecond)}/s`);
                if (percent >= 100) {
                    uploadTransferComplete = true;
                    setSingleUploadProcessingState();
                    return;
                }

                $('#singleUploadProgressEta').text(formatDuration(etaSeconds));
                $('#singleUploadProgressStatus').text('Uploading mod...');
            });

            xhr.upload.addEventListener('load', function() {
                if (!uploadTransferComplete) {
                    uploadTransferComplete = true;
                    setSingleUploadProcessingState();
                }
            });

            xhr.addEventListener('load', function() {
                $submitButton.prop('disabled', false).removeClass('is-loading');

                let payload = {};
                try {
                    payload = xhr.responseText ? JSON.parse(xhr.responseText) : {};
                } catch (error) {
                    console.error('Failed to parse single upload response', error);
                }

                if (xhr.status >= 200 && xhr.status < 300 && payload.ok) {
                    setSingleUploadProcessingState();
                    window.location.href = payload.redirect_url || window.location.pathname;
                    return;
                }

                resetSingleUploadProgress();
                const errorMessage = payload.error || 'Mod upload failed.';
                alert(errorMessage);
            });

            xhr.addEventListener('error', function() {
                $submitButton.prop('disabled', false).removeClass('is-loading');
                resetSingleUploadProgress();
                alert('Mod upload failed. Please try again.');
            });

            xhr.addEventListener('abort', function() {
                $submitButton.prop('disabled', false).removeClass('is-loading');
                resetSingleUploadProgress();
                alert('Mod upload was cancelled.');
            });

            xhr.send(formData);
        });

        $('#replaceModsForm').on('submit', function(event) {
            event.preventDefault();

            const formElement = this;
            const $form = $(formElement);
            const $submitButton = $('#replaceModsButton');
            const fileInput = formElement.querySelector('input[name="mods"]');

            if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
                return;
            }

            const files = Array.from(fileInput.files).filter((file) => file.name.toLowerCase().endsWith('.jar'));
            if (files.length === 0) {
                alert('No .jar mod files were found in the selected folder.');
                return;
            }

            const startTime = Date.now();
            const totalBytes = files.reduce((sum, file) => sum + (file.size || 0), 0);

            showBulkUploadProgress();
            $('#bulkUploadProgressStatus').text('Uploading mods...');
            $submitButton.prop('disabled', true).addClass('is-loading');

            const baseAction = $form.attr('action');

            (async function() {
                let uploadedBytes = 0;
                try {
                    const batchStart = await requestJson(`${baseAction}/start`);
                    const batchId = batchStart.batch_id;

                    for (let index = 0; index < files.length; index += 1) {
                        const file = files[index];
                        await uploadBulkBatchFile(`${baseAction}/file`, batchId, file, uploadedBytes, totalBytes, index + 1, files.length, startTime);
                        uploadedBytes += file.size || 0;
                    }

                    $('#bulkUploadProgressBar').val(100);
                    $('#bulkUploadProgressPercent').text('100%');
                    $('#bulkUploadProgressTransferred').text(`${formatBytes(totalBytes)} / ${formatBytes(totalBytes)}`);
                    $('#bulkUploadProgressSpeed').text(`${formatBytes(totalBytes / Math.max((Date.now() - startTime) / 1000, 0.1))}/s`);
                    setBulkUploadProcessingState();

                    const commitResponse = await requestJson(`${baseAction}/commit`, 'POST', new URLSearchParams({ batch_id: batchId }));
                    window.location.href = commitResponse.redirect_url || window.location.pathname;
                } catch (error) {
                    console.error('Bulk staged upload failed', error);
                    resetBulkUploadProgress();
                    alert(error.message || 'Bulk mod upload failed.');
                } finally {
                    $submitButton.prop('disabled', false).removeClass('is-loading');
                }
            })();
        });
        
        $('.file-input').on('change', function() 
        {
            const $fileNameDisplay = $(this).closest('.file-label').find('.file-name');
            const $form = $(this).closest('form');
            const $submitButton = $form.find('button[type="submit"]');
            
            if (this.files && this.files.length > 0) 
            {
                if ($(this).attr('name') === 'mods' && this.files.length > 1) {
                    $fileNameDisplay.text(`${this.files.length} files selected`);
                } else {
                    $fileNameDisplay.text(this.files[0].name);
                }
                $submitButton.prop('disabled', false).removeClass('is-loading');
            } 
            else 
            {
                $fileNameDisplay.text($(this).attr('name') === 'mods' ? 'No folder selected' : 'No file selected');
                $submitButton.prop('disabled', true);
            }
        });

        // Initialize button states on page load
        $('input.file-input').each(function() {
            const $form = $(this).closest('form');
            const $submitButton = $form.find('button[type="submit"]');
            
            if (!this.files || this.files.length === 0) {
                $submitButton.prop('disabled', true);
            }
        });

        const initialPlayerCount = $('#playerCountValue').data('player-count');
        const initialPlayerCapacity = $('#playerCountValue').data('player-capacity');
        renderStatus('{{spawn.get_status()}}');
        renderPlayerCount(initialPlayerCount, initialPlayerCapacity);

        // Poll for status updates every 3 seconds
        setInterval(function() {
            $.get(window.location.pathname + '/status', function(data) {
                try {
                    const response = typeof data === 'string' ? JSON.parse(data) : data;
                    const status = response.status;
                    renderStatus(status);
                    renderPlayerCount(response.player_count, response.player_capacity);
                } catch (e) {
                    console.error('Error updating status:', e);
                }
            }).fail(function() {
                console.error('Failed to fetch status');
            });
        }, 3000);
    });
</script>

<div class="container is-fluid p-4">
    %if page_error:
    <div class="notification is-danger">
        {{page_error}}
    </div>
    %end
    %if not can_manage:
    <div class="notification is-info">
        <span class="icon"><i class="fa-solid fa-lock"></i></span>
        This server is owned by <strong>{{spawn.owner}}</strong>. Log in as the owner or an admin to manage it.
    </div>
    %end
    %if not spawn.owner and user:
    <div class="notification is-info is-flex is-justify-content-space-between is-align-items-center is-flex-wrap-wrap">
        <span>
            <span class="icon"><i class="fa-solid fa-egg"></i></span>
            This server is unowned. Claim it to become its owner — only you and admins will be able to manage it. Claiming a running server uses one of your free eggs.
        </span>
        <form method="post" action="/spawn/{{spawn.name}}/claim">
            <button type="submit" class="button is-link">Claim server</button>
        </form>
    </div>
    %end
    <!-- Server Info Card -->
    <div class="columns is-multiline">
        <div class="column is-12-mobile is-6-tablet is-4-desktop">
            <div class="card">
                <div class="card-content">
                    <p class="title is-5">Server Info</p>
                    <table class="table is-narrow is-fullwidth">
                        <tbody>
                            <tr>
                                <td><strong>Name:</strong></td>
                                <td>{{spawn.name}}</td>
                            </tr>
                            <tr>
                                <td><strong>Status:</strong></td>
                                <td id="spawnStatusValue">
                                    %if spawn.get_status() == "running": 
                                        <span class="tag is-success">{{spawn.get_status()}}</span>
                                    %elif spawn.get_status() in ["created", "restarting", "removing", "paused", "exited"]:
                                        <span class="tag is-warning">{{spawn.get_status()}}</span>
                                    %else:
                                        <span class="tag is-danger">{{spawn.get_status()}}</span>
                                    %end
                                </td>
                            </tr>
                            <tr>
                                <td><strong>Port:</strong></td>
                                <td>{{spawn.port}}</td>
                            </tr>
                            <tr>
                                <td><strong>Owner:</strong></td>
                                <td>
                                    %if spawn.owner:
                                    <span class="tag is-info">{{spawn.owner}}</span>
                                    %else:
                                    <span class="tag">unowned</span>
                                    %end
                                </td>
                            </tr>
                            <tr>
                                <td><strong>Players Online:</strong></td>
                                <td id="playerCountValue" data-player-count="{{player_count if player_count is not None else ''}}" data-player-capacity="{{player_capacity if player_capacity is not None else ''}}">
                                    %if player_count is not None and player_capacity is not None:
                                        <span class="tag is-info">{{player_count}} / {{player_capacity}}</span>
                                    %elif player_count is not None:
                                        <span class="tag is-info">{{player_count}}</span>
                                    %else:
                                        <span class="has-text-grey">Unavailable</span>
                                    %end
                                </td>
                            </tr>
                            <tr>
                                <td><strong>Connect:</strong></td>
                                <td>
                                    <code>{{server_connection_host}}:{{spawn.port}}</code>
                                    <button id="copyAddressButton" type="button" class="button is-small is-link ml-2">
                                        <span class="icon"><i class="fas fa-copy"></i></span>
                                        <span>Copy</span>
                                    </button>
                                </td>
                            </tr>
                            <tr>
                                <td><strong>Type:</strong></td>
                                <td>{{spawn.type}}</td>
                            </tr>
                            <tr>
                                <td><strong>MC Version:</strong></td>
                                <td>{{spawn.minecraft_version}}</td>
                            </tr>
                            %if spawn.type == 'NEOFORGE':
                            <tr>
                                <td><strong>NeoForge:</strong></td>
                                <td>{{spawn.forge_version}}</td>
                            </tr>
                            %elif spawn.type == 'FORGE':
                            <tr>
                                <td><strong>Forge:</strong></td>
                                <td>{{spawn.forge_version}}</td>
                            </tr>
                            %end
                            <tr>
                                <td><strong>Loaded Mods:</strong></td>
                                <td>{{len(mods)}}</td>
                            </tr>
                            %if len(spawn.pending_mod_deletions) > 0:
                            <tr>
                                <td><strong>Pending Del:</strong></td>
                                <td><span class="tag is-warning">{{len(spawn.pending_mod_deletions)}}</span></td>
                            </tr>
                            %end
                        </tbody>
                    </table>
                </div>
                %if can_manage:
                <footer class="card-footer is-flex-wrap-wrap">
                    <form class="card-footer-item is-flex-grow-1" action="/spawn/{{spawn.name}}/recreate" method="post">
                        <button id="recreateButton" class="button is-info is-fullwidth">Re-create</button>
                    </form>
                    <form class="card-footer-item is-flex-grow-1" action="/spawn/{{spawn.name}}/start" method="post">
                        <button id="startButton" class="button is-success is-fullwidth">Start</button>
                    </form>
                    <form class="card-footer-item is-flex-grow-1" action="/spawn/{{spawn.name}}/stop" method="post">
                        <button id="stopButton" class="button is-warning is-fullwidth">Stop</button>
                    </form>
                    <form class="card-footer-item is-flex-grow-1" id="deleteForm" action="/spawn/{{spawn.name}}/delete" method="post">
                        <button id="deleteButton" type="button" class="button is-danger is-fullwidth">Delete</button>
                    </form>
                </footer>
                %end
            </div>
        </div>

        <!-- Mods Section -->
        <div class="column is-12-mobile is-6-tablet is-4-desktop">
            <div class="box">
                <h2 class="title is-5">Mods ({{len(mods)}})</h2>
                %if can_manage and len(mods) > 0:
                <form id="deleteAllModsForm" action="/spawn/{{spawn.name}}/mods/delete-all" method="post" class="mb-3">
                    <button id="deleteAllModsButton" type="button" class="button is-danger is-small is-fullwidth">
                        <span class="icon"><i class="fas fa-trash"></i></span>
                        <span>Delete All Mods</span>
                    </button>
                </form>
                %end
                %if len(mods) == 0:
                <p class="has-text-grey">No mods found.</p>
                %else:
                <div style="max-height: 250px; overflow-y: auto; border: 1px solid #dbdbdb; border-radius: 4px; padding: 0.5rem;">
                %for mod in mods:
                <form action="/spawn/{{spawn.name}}/mods/delete" method="post" class="mb-1">
                    <div class="field is-grouped is-grouped-multiline mb-1">
                        <div class="control is-expanded">
                            <input class="input is-small" type="text" name="mod" value="{{mod}}" readonly>
                        </div>
                        %if can_manage:
                        <div class="control">
                            <button class="button is-small is-danger">Delete</button>
                        </div>
                        %end
                    </div>
                </form>
                %end
                </div>
                %end

                %if can_manage:
                <form id="replaceModsForm" action="/spawn/{{spawn.name}}/mods/replace" method="post" enctype="multipart/form-data" class="mt-3">
                    <div class="field mb-2">
                        <label class="label is-small">Replace All Mods</label>
                        <div class="file has-name is-fullwidth">
                            <label class="file-label">
                                <input class="file-input" type="file" name="mods" multiple webkitdirectory directory accept=".jar" />
                                <span class="file-cta is-small">
                                    <span class="file-icon"><i class="fas fa-folder-open"></i></span>
                                    <span class="file-label">Choose folder</span>
                                </span>
                                <span class="file-name is-small">No folder selected</span>
                            </label>
                        </div>
                    </div>
                    <div id="bulkUploadProgressWrapper" class="box is-hidden p-3 mb-3">
                        <div class="is-flex is-justify-content-space-between is-align-items-center mb-2">
                            <span id="bulkUploadProgressStatus" class="has-text-weight-semibold">Preparing upload...</span>
                            <span id="bulkUploadProgressPercent" class="tag is-info">0%</span>
                        </div>
                        <progress id="bulkUploadProgressBar" class="progress is-primary mb-2" value="0" max="100">0%</progress>
                        <div class="is-size-7 has-text-grey">
                            <div><strong>Transferred:</strong> <span id="bulkUploadProgressTransferred">0 B / 0 B</span></div>
                            <div><strong>Speed:</strong> <span id="bulkUploadProgressSpeed">0 B/s</span></div>
                            <div><strong>ETA:</strong> <span id="bulkUploadProgressEta">Waiting...</span></div>
                        </div>
                    </div>
                    <button type="submit" id="replaceModsButton" class="button is-primary is-fullwidth is-small">
                        <span class="icon"><i class="fas fa-sync"></i></span>
                        <span>Replace Mods</span>
                    </button>
                </form>

                <form id="addModForm" action="/spawn/{{spawn.name}}/mods/add-file" method="post" enctype="multipart/form-data" class="mt-3">
                    <div class="field mb-2">
                        <label class="label is-small">Add Single Mod</label>
                        <div class="file has-name is-fullwidth">
                            <label class="file-label">
                                <input class="file-input" type="file" name="mod" accept=".jar" />
                                <span class="file-cta is-small">
                                    <span class="file-icon"><i class="fas fa-upload"></i></span>
                                    <span class="file-label">Choose mod</span>
                                </span>
                                <span class="file-name is-small">No file selected</span>
                            </label>
                        </div>
                    </div>
                    <div id="singleUploadProgressWrapper" class="box is-hidden p-3 mb-3">
                        <div class="is-flex is-justify-content-space-between is-align-items-center mb-2">
                            <span id="singleUploadProgressStatus" class="has-text-weight-semibold">Preparing upload...</span>
                            <span id="singleUploadProgressPercent" class="tag is-info">0%</span>
                        </div>
                        <progress id="singleUploadProgressBar" class="progress is-info mb-2" value="0" max="100">0%</progress>
                        <div class="is-size-7 has-text-grey">
                            <div><strong>Transferred:</strong> <span id="singleUploadProgressTransferred">0 B / 0 B</span></div>
                            <div><strong>Speed:</strong> <span id="singleUploadProgressSpeed">0 B/s</span></div>
                            <div><strong>ETA:</strong> <span id="singleUploadProgressEta">Waiting...</span></div>
                        </div>
                    </div>
                    <button type="submit" id="addModButton" class="button is-info is-fullwidth is-small">Add Mod</button>
                </form>
                %end
            </div>
        </div>

        <div id="deleteAllModsConfirmModal" class="modal">
            <div class="modal-background"></div>
            <div class="modal-card">
                <header class="modal-card-head">
                    <p class="modal-card-title">Delete All Mods</p>
                    <button class="delete" type="button" aria-label="close"></button>
                </header>
                <section class="modal-card-body">
                    <p>This will remove all mod files from this server.</p>
                    <p class="mt-3 has-text-weight-semibold">A restart or re-create will still be required to fully apply the removal.</p>
                </section>
                <footer class="modal-card-foot is-justify-content-flex-end">
                    <button id="cancelDeleteAllModsButton" type="button" class="button">Cancel</button>
                    <button id="confirmDeleteAllModsButton" type="button" class="button is-danger">Delete All Mods</button>
                </footer>
            </div>
        </div>

        <!-- Backups Section -->
        <div class="column is-12-mobile is-6-tablet is-4-desktop">
            <div class="box">
                <h2 class="title is-5">Backups</h2>
                %if can_manage:
                <form action="/spawn/{{spawn.name}}/backup/create" method="post" onsubmit="showLoadingModal('Creating backup. Please wait...');">
                    <div class="field mb-2">
                        <label class="label is-small">Backup Name (optional)</label>
                        <div class="control">
                            <input class="input is-small" type="text" name="backup_name" placeholder="{{default_backup_name}}">
                        </div>
                    </div>
                    <button type="submit" class="button is-success is-fullwidth mb-3">
                        <span class="icon"><i class="fas fa-save"></i></span>
                        <span>Create Backup</span>
                    </button>
                </form>

                <h3 class="subtitle is-6">Schedule</h3>
                <form action="/spawn/{{spawn.name}}/backup/settings" method="post" onsubmit="showLoadingModal('Saving settings. Please wait...');">
                    <div class="field">
                        <label class="checkbox is-small">
                            %if spawn.backup_settings.get('daily_backup_enabled'):
                            <input type="checkbox" id="daily_backup_enabled" name="daily_backup_enabled" value="on" checked>
                            %else:
                            <input type="checkbox" id="daily_backup_enabled" name="daily_backup_enabled" value="on">
                            %end
                            <span>Enable daily backups</span>
                        </label>
                    </div>

                    <label class="label is-small">Time</label>
                    <div class="field is-grouped mb-2">
                        <div class="control is-expanded">
                            <input class="input is-small" type="number" name="daily_backup_hour" min="0" max="23" value="{{spawn.backup_settings.get('daily_backup_hour', 2)}}" placeholder="HH">
                        </div>
                        <div class="control is-expanded">
                            <input class="input is-small" type="number" name="daily_backup_minute" min="0" max="59" value="{{spawn.backup_settings.get('daily_backup_minute', 0)}}" placeholder="MM">
                        </div>
                    </div>

                    <label class="label is-small">Keep (days)</label>
                    <div class="field mb-3">
                        <div class="control is-expanded">
                            <input class="input is-small" type="number" name="retention_days" min="1" value="{{spawn.backup_settings.get('retention_days', 7)}}" placeholder="Days">
                        </div>
                    </div>

                    <button type="submit" class="button is-info is-fullwidth is-small">Save</button>
                </form>
                %else:
                <p class="has-text-grey">Backup actions are reserved for the server's owner.</p>
                %end

                %if spawn.backup_settings.get('last_backup_timestamp'):
                <div class="content mt-2">
                    <small class="has-text-grey">Last: {{spawn.backup_settings.get('last_backup_timestamp')}}</small>
                </div>
                %end
            </div>
        </div>
    </div>

    <!-- Logs Section -->
    <div class="columns is-multiline mt-2">
        <div class="column is-12-mobile is-12-tablet is-6-desktop">
            <div class="box">
                <h2 class="title is-5">Logs</h2>
                <div class="buttons are-small mb-3">
                    %if can_manage:
                    <button id="analyzeLogsButton" type="button" class="button is-primary">
                        <span class="icon"><i class="fas fa-wand-magic-sparkles"></i></span>
                        <span>Analyze</span>
                    </button>
                    %end
                    <button id="streamButton" class="button is-outlined is-info">
                        <span class="icon"><i class="fas fa-broadcast-tower"></i></span>
                        <span>Stream</span>
                    </button>
                    <button id="refreshLogButton" type="button" class="button is-link">
                        <span class="icon"><i class="fas fa-sync"></i></span>
                        <span>Refresh</span>
                    </button>
                    <a href="/spawn/{{spawn.name}}/logs" class="button is-ghost">
                        <span class="icon"><i class="fas fa-expand"></i></span>
                        <span>Full</span>
                    </a>
                </div>
                <div id="logsContainer" style="max-height: 400px; overflow-y: auto; background: #f5f5f5; padding: 1rem; border-radius: 4px; border: 1px solid #dbdbdb;">
                    <pre id="logsContent" style="margin: 0; font-size: 0.8em; font-family: 'Courier New', monospace; white-space: pre-wrap; word-wrap: break-word;">{{spawn.logs}}</pre>
                </div>
                %if can_manage:
                <form action="/spawn/{{spawn.name}}/console/send" method="post" class="mt-3">
                    <div class="field is-grouped">
                        <div class="control is-expanded">
                            <input class="input is-small" type="text" name="consoleCommand" placeholder="Console command...">
                        </div>
                        <div class="control">
                            <button class="button is-small is-link">Send</button>
                        </div>
                    </div>
                </form>
                %end
            </div>
        </div>

        <!-- Server Properties Section -->
        <div class="column is-12-mobile is-12-tablet is-6-desktop">
            <div class="box">
                <div class="level mb-3">
                    <div class="level-left">
                        <div class="level-item">
                            <h2 class="title is-5">Server Properties</h2>
                        </div>
                    </div>
                    %if can_manage:
                    <div class="level-right">
                        <div class="level-item">
                            <form action="/spawn/{{spawn.name}}/server_properties/save" method="post" style="display: inline;">
                                <button id="updateServerPropertiesButton" class="button is-small is-link">Update & Restart</button>
                            </form>
                        </div>
                    </div>
                    %end
                </div>
                %if can_manage:
                <form action="/spawn/{{spawn.name}}/server_properties/save" method="post">
                    <textarea class="textarea" name="server_properties" rows="16" style="font-family: 'Courier New', monospace; font-size: 0.85em;">{{spawn.server_properties}}</textarea>
                </form>
                %else:
                <textarea class="textarea" rows="16" readonly style="font-family: 'Courier New', monospace; font-size: 0.85em;">{{spawn.server_properties}}</textarea>
                %end
            </div>
        </div>
    </div>

    <!-- Backups List Section -->
    %if len(spawn.list_backups()) > 0:
    <div class="columns is-multiline mt-2">
        <div class="column is-12">
            <div class="box">
                <h2 class="title is-5">Existing Backups ({{len(spawn.list_backups())}})</h2>
                <div class="table-container">
                    <table class="table is-fullwidth is-striped">
                        <tbody>
                        %for backup in spawn.list_backups():
                            <tr>
                                <td>
                                    <div>
                                        <strong>{{backup['name']}}</strong>
                                        <span class="tag is-dark is-rounded">{{backup['type']}}</span>
                                        <br>
                                        <small class="has-text-grey">{{backup['timestamp']}} ({{backup['size_mb']}} MB)</small>
                                    </div>
                                </td>
                                %if can_manage:
                                <td class="is-narrow">
                                    <form action="/spawn/{{spawn.name}}/backup/restore/{{backup['name']}}" method="post" style="display: inline;" onsubmit="if(!confirm('Restore this backup? Current world will be replaced.')) return false; showLoadingModal('Restoring backup. Please wait...');return true;">
                                        <button type="submit" class="button is-small is-info">
                                            <span class="icon"><i class="fas fa-undo"></i></span>
                                        </button>
                                    </form>
                                </td>
                                <td class="is-narrow">
                                    <form action="/spawn/{{spawn.name}}/backup/delete/{{backup['name']}}" method="post" style="display: inline;" onsubmit="if(!confirm('Delete this backup?')) return false; showLoadingModal('Deleting backup. Please wait...');return true;">
                                        <button type="submit" class="button is-small is-danger">
                                            <span class="icon"><i class="fas fa-trash"></i></span>
                                        </button>
                                    </form>
                                </td>
                                %end
                            </tr>
                        %end
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    %end
</div>

<div class="modal" id="logAnalysisModal">
    <div class="modal-background"></div>
    <div class="modal-card">
        <header class="modal-card-head">
            <p class="modal-card-title" id="logAnalysisModalTitle">Log Analysis</p>
            <button class="delete" id="closeLogAnalysisModal" aria-label="close"></button>
        </header>
        <section class="modal-card-body">
            <article class="message is-info" id="logAnalysisMessage">
                <div class="message-body" id="logAnalysisBody"></div>
            </article>
        </section>
        <footer class="modal-card-foot">
            <button class="button" id="dismissLogAnalysisModal">Close</button>
        </footer>
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
