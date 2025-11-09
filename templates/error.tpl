%include('./templates/header.tpl')

<section class="hero is-danger is-fullheight-with-navbar">
    <div class="hero-body">
        <div class="container has-text-centered">
            <div class="columns is-centered">
                <div class="column is-6">
                    <div class="box">
                        <h1 class="title is-1 has-text-danger">
                            <span class="icon is-large">
                                <i class="fas fa-exclamation-triangle"></i>
                            </span>
                        </h1>
                        <h2 class="title is-3">Error</h2>
                        <p class="subtitle is-5 mb-5">{{error_message}}</p>
                        %if details:
                        <div class="notification is-light">
                            <p class="has-text-left">{{details}}</p>
                        </div>
                        %end
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
                            <a href="javascript:history.back()" class="button is-light is-medium">
                                <span class="icon">
                                    <i class="fas fa-arrow-left"></i>
                                </span>
                                <span>Go Back</span>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

%include('./templates/footer.tpl')
