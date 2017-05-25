// Like post
$('article').on('click', '.like-btn', function(e){
	e.preventDefault();
	var pid = $(this).parent().data('pid');
	var $counter = $(this).find('.counter');
	var $likeBtn = $(this);
	$.ajax({
		type: 'POST',
		url: '/blog/'+pid,
		dataType: 'json',
		success: function(response){
			$likeBtn.html(response['btn_txt']+'<span class="heart">  &#x2764; </span><span class="counter">'
							+response['likes_counter']+'</span>')
			if (response['message']){
				alert(response['message']);}}});
});

//Delete post
$('article').on('click', '.del-post', function(e){
	e.preventDefault();
	var pid = $('.post-heading').data('pid');
	if (confirm('Are you sure you want to delete this post?') == true){
		$.ajax({
			type: 'POST',
			url: '/blog/'+pid+'/delete',
			dataType: 'json',
			success: function(response){
				alert(response['message']);
				window.location.href = '/';}});}
});

// Create new comment
$(document).ready(function(){
	$('.new-comment').hide();
	$('#new-comment-btn').click(function(e){
		$('.new-comment').toggle('slow');
		// Submit comments, write to database and dynamically update on client side
		$('#new-comment-form').submit(function(e){
			e.preventDefault();
			$('.new-comment').fadeOut('slow');
			var pid = $('.post-heading').data('pid');
			var dt = new Date();
			var dtStr = dt.toLocaleString('en-us', {month: 'short', day: 'numeric', year: 'numeric'});
			var comment = $('#new-comment-input').val();
			$.ajax({
				type: 'POST',
				url: '/blog/'+pid+'/comment',
				dataType: 'json',
				data: {'comment': comment},
				success: function(response){
					$('#new-comment-input').val(''); // reset comment input textarea
					var cid = response['cid'], 
						author = response['comm_author'], 
						content = response['comm_content'];
					$('.post-comments').prepend($('.post-comments').html());
					var $newItem = $('.post-comments li').first();
					$newItem.find('.info-line').html(
						'<span>'+author+' wrote: </span><span>'+dtStr+'</span>');
					$newItem.find('p').text(content);
					$newItem.data('cid', cid);}});
		});
	});
});

$('#new-comment-form .cancel-btn').click(function(e){
	e.preventDefault();
	$('.new-comment').fadeOut('slow');
})
// Edit comment
// Initially set comment item that is associated with previously clicked "edit" button to null.
var $prev = null;
function toggleComment(curr){
	curr.find('.comment-form, .comment-body').toggle();
	if ($prev && $prev.data('cid') != curr.data('cid')){
		$prev.find('.comment-form').hide();
		$prev.find('.comment-body').show();}
	$prev = curr;
}
$('.post-comments').on('click', '.edit-btn', function(e){
/*	Event delegation: you are delegating the job of the event listener to a
	parent of these elements. Works with new element: if you add new elements 
	to the DOM tree, you do not have to add event handlers to the new elements 
	because the job has been delegated to an ancestor. by attaching an event listener 
	to a containing element, you are only responding to one element rather than 
	having an event handler for each child element. */
	e.preventDefault();
	var $currItem = $(this).closest('.comment-item');
	var cid = $currItem.data('cid');
	var content = $currItem.find('.content').text();
	
	toggleComment($currItem);
	$currItem.find('textarea').text(content);
});

$('.post-comments').on('click', '.save-btn', function(e){
	e.preventDefault();
	var pid = $('.post-heading').data('pid');
	
	var $savedItem = $(this).closest('.comment-item');
	var cid = $savedItem.data('cid');
	var editInput = $(this).prev().val();

	toggleComment($savedItem);
	$savedItem.find('.content').text(editInput);
	$.ajax({
		type: 'POST',
		url: '/blog/'+pid+'/comment',
		dataType: 'json',
		data: {"comment_id": cid, "comment": editInput}
	});
});

$('.post-comments').on('click', '.cancel-btn', function(e){
	e.preventDefault();
	$(this).parent().toggle();
});

// Delete comment
$('.post-comments').on('click', '.del-comment', function(e){
	e.preventDefault();
	var pid = $('.post-heading').data('pid');

	var $currItem = $(this).closest('.comment-item');
	var cid = $currItem.data('cid');
	$.ajax({
		type: 'POST',
		url: '/blog/'+pid+'/comment/delete',
		dataType: 'json',
		data: {"comment_id": cid},
		success: function(response){
			if (response['error']){
				alert(response['error']);
			}else{
				$currItem.remove();}}});
});