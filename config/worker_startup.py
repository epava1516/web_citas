"""Prepare immutable Django structures before a Gunicorn worker serves requests."""


def prepare_static_structures():
    from django.template.loader import get_template
    from django.urls import resolve, reverse
    from django.utils.translation import override

    for language in ('es', 'en'):
        with override(language):
            resolve('/' + language + '/')
            resolve('/' + language + '/listing/00000000-0000-0000-0000-000000000000/')
            reverse('home')
            for name in ('base.html', 'listings/results.html', 'listings/public_detail.html'):
                get_template(name)


def post_worker_init(worker):
    prepare_static_structures()
    worker.log.info('Static routes and templates prepared for worker pid=%s', worker.pid)
