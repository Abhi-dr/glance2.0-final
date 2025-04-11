$( '.js-filter' ).on( 'click', function() {
  
    var $color = $(this).attr('data-filter');
    
    if ( $color == 'all' ) {
      $( '.js-filterable' ).removeClass( 'is-hidden' );    
    } else {
      $( '.js-filterable' ).addClass( 'is-hidden' );
      $( '.js-filterable[data-filter=' + $color + ']' ).removeClass( 'is-hidden' );
    }
    
  });