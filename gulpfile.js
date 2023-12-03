const gulp = require('gulp')
// const copy = require('gulp-copy')
// const concat = require('gulp-concat')

gulp.task('animate', () => {
    return gulp
        .src('node_modules/animate.css/animate.min.css')
        .pipe(gulp.dest('app/static/dist/animate'))
})

gulp.task('bootstrap', () => {
    return gulp
        .src([
            'node_modules/bootstrap/dist/css/bootstrap.min.css',
            'node_modules/bootstrap/dist/js/bootstrap.bundle.min.js',
        ])
        .pipe(gulp.dest('app/static/dist/bootstrap'))
})

gulp.task('clipboard', () => {
    return gulp
        .src('node_modules/clipboard/dist/clipboard.min.js')
        .pipe(gulp.dest('app/static/dist/clipboard'))
})

gulp.task('fontawesome', () => {
    return gulp
        .src(
            [
                'node_modules/@fortawesome/fontawesome-free/css/all.min.css',
                'node_modules/@fortawesome/fontawesome-free/js/all.min.js',
                'node_modules/@fortawesome/fontawesome-free/webfonts/**/*',
            ],
            { base: 'node_modules/@fortawesome/fontawesome-free' }
        )
        .pipe(gulp.dest('app/static/dist/fontawesome'))
})

gulp.task('js-cookie', () => {
    return gulp
        .src('node_modules/js-cookie/dist/js.cookie.min.js')
        .pipe(gulp.dest('app/static/dist/js-cookie'))
})

gulp.task('jquery', () => {
    return gulp
        .src('node_modules/jquery/dist/jquery.min.js')
        .pipe(gulp.dest('app/static/dist/jquery'))
})

gulp.task('swagger-ui', () => {
    return gulp
        .src([
            'node_modules/swagger-ui/dist/swagger-ui.css',
            'node_modules/swagger-ui/dist/swagger-ui-bundle.js',
            'node_modules/swagger-ui/dist/swagger-ui-standalone-preset.js',
        ])
        .pipe(gulp.dest('app/static/dist/swagger-ui'))
})

gulp.task('swagger-yaml', () => {
    return gulp.src(['swagger.yaml']).pipe(gulp.dest('app/static/dist/'))
})

gulp.task(
    'default',
    gulp.parallel(
        'animate',
        'bootstrap',
        'clipboard',
        'fontawesome',
        'js-cookie',
        'jquery',
        'swagger-ui',
        'swagger-yaml'
    )
)
