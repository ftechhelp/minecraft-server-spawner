%include('./templates/header.tpl')

<section class="section">
    <div class="container" style="max-width: 420px;">
        <div class="box">
            <h1 class="title is-4 has-text-centered">Log in</h1>

            %if login_error:
            <div class="notification is-danger is-light">
                {{login_error}}
            </div>
            %end

            <form method="post" action="/login">
                <input type="hidden" name="next" value="{{next_url}}">
                <div class="field">
                    <label class="label">Username</label>
                    <div class="control has-icons-left">
                        <input class="input" type="text" name="username" placeholder="Username" required autofocus>
                        <span class="icon is-small is-left"><i class="fa-solid fa-user"></i></span>
                    </div>
                </div>
                <div class="field">
                    <label class="label">Password</label>
                    <div class="control has-icons-left">
                        <input class="input" type="password" name="password" placeholder="Password" required>
                        <span class="icon is-small is-left"><i class="fa-solid fa-lock"></i></span>
                    </div>
                </div>
                <div class="field">
                    <div class="control">
                        <button type="submit" class="button is-primary is-fullwidth">Log in</button>
                    </div>
                </div>
            </form>
            <p class="has-text-grey has-text-centered is-size-7 mt-3">
                No account? Ask an admin to create one for you.
            </p>
        </div>
    </div>
</section>

%include('./templates/footer.tpl')
