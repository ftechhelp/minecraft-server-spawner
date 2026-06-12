%include('./templates/header.tpl')

<section class="section">
    <div class="container">
        <h1 class="title is-3">User Management</h1>

        %if notice:
        <div class="notification is-success is-light">
            {{notice}}
        </div>
        %end
        %if page_error:
        <div class="notification is-danger is-light">
            {{page_error}}
        </div>
        %end

        <div class="box">
            <h2 class="title is-5">Add a user</h2>
            <form method="post" action="/admin/users/create">
                <div class="columns">
                    <div class="column">
                        <input class="input" type="text" name="username" placeholder="Username" required>
                    </div>
                    <div class="column">
                        <input class="input" type="password" name="password" placeholder="Password" required>
                    </div>
                    <div class="column is-2">
                        <input class="input" type="number" name="eggs" placeholder="Eggs" min="0" value="1">
                    </div>
                    <div class="column is-2">
                        <label class="checkbox mt-2">
                            <input type="checkbox" name="is_admin">
                            Admin
                        </label>
                    </div>
                    <div class="column is-2">
                        <button type="submit" class="button is-primary is-fullwidth">Create</button>
                    </div>
                </div>
            </form>
        </div>

        <div class="box">
            <h2 class="title is-5">Users</h2>
            <table class="table is-fullwidth is-striped">
                <thead>
                    <tr>
                        <th>Username</th>
                        <th>Eggs <span class="icon has-text-warning"><i class="fa-solid fa-egg"></i></span></th>
                        <th>Role</th>
                        <th>Created</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    %for account in users_list:
                    <tr>
                        <td class="is-vcentered">
                            {{account['name']}}
                            %if user and account['name'] == user['name']:
                            <span class="tag is-info is-light">you</span>
                            %end
                        </td>
                        <td>
                            <form method="post" action="/admin/users/{{account['name']}}/eggs" class="field has-addons">
                                <div class="control">
                                    <input class="input is-small" type="number" name="eggs" min="0" value="{{account['eggs']}}" style="width: 80px;">
                                </div>
                                <div class="control">
                                    <button type="submit" class="button is-small is-link">Save</button>
                                </div>
                            </form>
                        </td>
                        <td class="is-vcentered">
                            %if account['is_admin']:
                            <span class="tag is-warning">Admin</span>
                            %else:
                            <span class="tag">User</span>
                            %end
                        </td>
                        <td class="is-vcentered">{{account.get('created_at', '')[:10]}}</td>
                        <td>
                            <div class="buttons are-small is-right">
                                <form method="post" action="/admin/users/{{account['name']}}/toggle-admin">
                                    <button type="submit" class="button is-small">
                                        {{'Demote to user' if account['is_admin'] else 'Promote to admin'}}
                                    </button>
                                </form>
                                <form method="post" action="/admin/users/{{account['name']}}/delete" onsubmit="return confirm('Delete user {{account['name']}}? Their servers will become unowned.');">
                                    <button type="submit" class="button is-small is-danger">Delete</button>
                                </form>
                            </div>
                        </td>
                    </tr>
                    %end
                </tbody>
            </table>
        </div>
    </div>
</section>

%include('./templates/footer.tpl')
