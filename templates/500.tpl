%include('./templates/header.tpl')

<section class="hero is-danger is-fullheight-with-navbar">
    <div class="hero-body">
        <div class="container has-text-centered">
            <div class="columns is-centered">
                <div class="column is-6">
                    <div class="box">
                        <h1 class="title is-1 has-text-danger">
                            <span class="icon is-large">
                                <i class="fas fa-server"></i>
                            </span>
                        </h1>
                        <h2 class="title is-2">500</h2>
                        <h3 class="subtitle is-4">Internal Server Error</h3>
                        <p class="mb-5">{{error_message if error_message else "Something went wrong on our end. We're working to fix it."}}</p>
                        <div class="notification is-light">
                            <p class="has-text-weight-semibold mb-2">What you can try:</p>
                            <ul class="has-text-left">
                                <li>• Refresh the page and try again</li>
                                <li>• Check if Docker is running</li>
                                <li>• Verify that the spawn configuration is valid</li>
                                <li>• Check the application logs for more details</li>
                            </ul>
                        </div>
                        %if suggested_action:
                        <div class="notification is-info is-light">
                            <p class="has-text-weight-semibold">Suggested Action:</p>
                            <p>{{suggested_action}}</p>
                        </div>
                        %end
                        <div class="buttons is-centered mt-5">
                            <a href="/" class="button is-primary is-medium">
                                <span class="icon">
                                    <i class="fas fa-home"></i>
                                </span>
                                <span>Go to Home</span>
                            </a>
                            <a href="javascript:location.reload()" class="button is-light is-medium">
                                <span class="icon">
                                    <i class="fas fa-sync"></i>
                                </span>
                                <span>Retry</span>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

%include('./templates/footer.tpl')
