%include('./templates/header.tpl')

<section class="hero is-warning is-fullheight-with-navbar">
    <div class="hero-body">
        <div class="container has-text-centered">
            <div class="columns is-centered">
                <div class="column is-6">
                    <div class="box">
                        <h1 class="title is-1 has-text-warning">
                            <span class="icon is-large">
                                <i class="fas fa-search"></i>
                            </span>
                        </h1>
                        <h2 class="title is-2">404</h2>
                        <h3 class="subtitle is-4">Not Found</h3>
                        <p class="mb-5">{{error_message if error_message else "The spawn or resource you're looking for doesn't exist."}}</p>
                        <div class="notification is-info is-light">
                            <p>The spawn may have been deleted or the URL might be incorrect.</p>
                        </div>
                        <div class="buttons is-centered mt-5">
                            <a href="/" class="button is-primary is-medium">
                                <span class="icon">
                                    <i class="fas fa-home"></i>
                                </span>
                                <span>Go to Home</span>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

%include('./templates/footer.tpl')
