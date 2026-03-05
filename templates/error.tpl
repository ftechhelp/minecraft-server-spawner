%include('./templates/header.tpl')

<section class="section">
    <div class="container">
        <div class="columns is-centered">
            <div class="column is-12-mobile is-10-tablet is-8-desktop">
                <div class="box">
                    <h1 class="title is-2 has-text-danger">
                        <span class="icon mr-2"><i class="fas fa-bug"></i></span>
                        <span>{{title}}</span>
                    </h1>

                    <p class="subtitle is-5">{{friendly_message}}</p>

                    <article class="message is-warning">
                        <div class="message-header">
                            <p>Help Uncle Vince troubleshoot</p>
                        </div>
                        <div class="message-body">
                            <p class="mb-2">
                                Please send Uncle Vince the details below so he can investigate quickly:
                            </p>
                            <p><strong>Status:</strong> {{status_code}}</p>
                            <p><strong>Details:</strong></p>
                            <pre class="mt-2" style="white-space: pre-wrap; word-break: break-word;">{{details}}</pre>
                        </div>
                    </article>

                    <div class="buttons">
                        <a href="/" class="button is-link">
                            <span class="icon"><i class="fas fa-home"></i></span>
                            <span>Back to Home</span>
                        </a>
                        <a href="/docs" class="button is-light">
                            <span class="icon"><i class="fas fa-book"></i></span>
                            <span>Open Documentation</span>
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

%include('./templates/footer.tpl')
