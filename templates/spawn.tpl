%include('./templates/header.tpl')

<div class="columns">
    <div class="column is-4">
        <div class="card">
            <div class="card-content">
                <p class="title">
                    <table class="table is-striped">
                        <tbody>
                            <tr>
                                <td>
                                    <h4 class="subtitle is-4">Status:</h4>
                                </td>
                                <td>
                                    <h4 class="subtitle is-4 has-text-primary">{{spawn.get_status()}}</h4>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </p>
            </div>
            <footer class="card-footer">
                <p class="card-footer-item">
                    <a href="">Restart</a>
                </p>
                <p class="card-footer-item">
                    <a href="">Delete</a>
                </p>
            </footer>
        </div>
    </div>
</div>

%include('./templates/footer.tpl')