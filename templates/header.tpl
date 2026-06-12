<!DOCTYPE HTML>
<html>
    <head>
        <meta charset=utf-8">
        <title>Forge Spawner</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@1.0.1/css/bulma.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>
        <style>
            .loading-spinner { display: inline-block; width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            /* Used eggs: the glyph is split into two clipped pieces left in place, with a thin
               zigzag gap between them so the background shows through as a subtle crack line */
            .egg-cracked { position: relative; opacity: 0.55; }
            .egg-cracked .egg-piece { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; }
            .egg-cracked .egg-piece-top {
                clip-path: polygon(0% 0%, 100% 0%, 100% 30%, 75% 40%, 55% 26%, 35% 42%, 15% 30%, 0% 38%);
            }
            .egg-cracked .egg-piece-bottom {
                clip-path: polygon(0% 45%, 15% 37%, 35% 49%, 55% 33%, 75% 47%, 100% 37%, 100% 100%, 0% 100%);
            }
        </style>
        <script>
            function showLoadingModal(message = 'Please wait...') {
                $('#loadingModalText').text(message);
                $('#loadingModal').addClass('is-active');
            }
            function hideLoadingModal() {
                $('#loadingModal').removeClass('is-active');
            }
        </script>
    </head>
    <body>
        <!-- Loading Modal -->
        <div id="loadingModal" class="modal">
            <div class="modal-background"></div>
            <div class="modal-card">
                <div class="modal-card-body" style="text-align: center; padding: 3rem;">
                    <div class="loading-spinner"></div>
                    <p id="loadingModalText" class="mt-4 has-text-grey">Please wait...</p>
                </div>
            </div>
        </div>
        %include('./templates/navbar.tpl')