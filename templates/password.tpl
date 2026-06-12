%include('./templates/header.tpl')

<section class="section">
    <div class="container" style="max-width: 420px;">
        <div class="box">
            <h1 class="title is-4 has-text-centered">Set a new password</h1>

            %if forced:
            <div class="notification is-info">
                <span class="icon"><i class="fa-solid fa-lock"></i></span>
                This is your first login, so you need to choose your own password before continuing.
            </div>
            %end

            %if password_error:
            <div class="notification is-danger">
                {{password_error}}
            </div>
            %end

            <form method="post" action="/password">
                <input type="hidden" name="next" value="{{next_url}}">
                <div class="field">
                    <label class="label">New password</label>
                    <div class="control has-icons-left">
                        <input class="input" type="password" name="new_password" placeholder="New password" required autofocus>
                        <span class="icon is-small is-left"><i class="fa-solid fa-lock"></i></span>
                    </div>
                </div>
                <div class="field">
                    <label class="label">Confirm new password</label>
                    <div class="control has-icons-left">
                        <input class="input" type="password" name="confirm_password" placeholder="Confirm new password" required>
                        <span class="icon is-small is-left"><i class="fa-solid fa-lock"></i></span>
                    </div>
                </div>
                <div class="field">
                    <div class="control">
                        <button type="submit" class="button is-primary is-fullwidth">Save password</button>
                    </div>
                </div>
            </form>
        </div>
    </div>
</section>

%include('./templates/footer.tpl')
