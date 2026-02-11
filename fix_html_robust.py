import re

file_path = r'c:\Users\ADMIN\Documents\GitHub\instagram-reels\index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# exact string from the file (lines 132-148 roughly)
# matches <div class="videoFooter__actions"> ... </div> (closing actions)
# We also include the following default closing </div> of videoFooter to be sure we place sidebar outside.
# But wait, the previous regex failed because of nesting.
# Let's construct the bad block string line by line to match exactly.

bad_block_lines = [
    '            <div class="videoFooter__actions">',
    '              <div class="videoFooter_w_actionsLeft">',
    '                <button class="likebutton"> <i class="fa-solid fa-heart"></i></i> </button>',
    '                <div class="commentbutton"> <i class="fa-solid fa-message"></i> </div>',
    '                <div class="sharebutton"> <i class="fa-solid fa-share"></i> </div>',
    '              </div>',
    '              <div class="videoFooter__actionsRight">',
    '                <div class="videoFooter__stat">',
    '                  <div class="likedbutton"> <i class="fa-solid fa-heart"></i> </div>',
    '                  <p>12</p>',
    '                </div>',
    '                <div class="videoFooter__stat">',
    '                  <span class="commentsbutton"> <i class="fa-solid fa-message"></i> </span>',
    '                  <p>20</p>',
    '                </div>',
    '              </div>',
    '            </div>'
]

bad_block = "\n".join(bad_block_lines)

# The sidebar HTML to insert
sidebar_html = """
        <div class="videoSidebar">
          <div class="videoSidebar__button">
            <span class="material-icons"> favorite_border </span>
            <p>12k</p>
          </div>

          <div class="videoSidebar__button" onclick="showComments()">
            <span class="material-icons"> message </span>
            <p>230</p>
          </div>

          <div class="videoSidebar__button">
            <span class="material-icons"> share </span>
            <p>Share</p>
          </div>
        </div>"""

# We want to replace:
# bad_block
# followed by spacing and </div> (closing videoFooter)
# with:
# </div> (closing videoFooter)
# sidebar_html

# But indentation might vary slightly? From view_file it looks consistent.
# Let's try replacing just the bad_block with nothing?
# If we replace bad_block with "", we are left with empty lines and then </div>.
# Then the Sidebar is missing.
# We want to INSERT the sidebar AFTER the videoFooter.
# So we can replace `bad_block` with NOTHING.
# AND THEN we need to find where videoFooter ends and insert sidebar.
# BUT, that requires knowing which videoFooter we just modified.

# Better strategy: Replace (bad_block + next closing div) with (closing div + sidebar)
# Since the bad_block is inside videoFooter, the next </div> after it IS the videoFooter's closing tag.
# Let's find matches for bad_block.

# Read file content as lines to handle whitespace robustly?
# String replace is safest if we match exactly.
# Let's verify the bad_block matches in the content.

if bad_block in content:
    print(f"Found bad block occurrences: {content.count(bad_block)}")
    
    # We replace the bad_block with nothing (removing it from inside videoFooter)
    # AND we assume the sidebar needs to be added.
    # But wait, if we just remove it, we don't add the sidebar.
    
    # Let's try to match the context:
    # </div> (of videoFooter__ticker)
    # \s*
    # bad_block
    # \s*
    # </div> (of videoFooter)
    
    # And replace with:
    # </div> (of ticker)
    # </div> (of videoFooter)
    # sidebar_html
    
    # Ticker closing div:
    ticker_close = '            </div>'
    
    full_search_block = ticker_close + '\n\n' + bad_block
    # Note: there might be empty lines.
    
    # Let's normalize whitespace for search? No, risky.
    # Let's try to just replace `bad_block` with `</div>\n{sidebar_html}\n<div style="display:none">` ?? No that breaks HTML.
    
    # Correct appreach:
    # Replace `bad_block` with `` (empty).
    # This leaves the videoFooter containing only ticker (and footerText).
    # THEN, we look for `<!-- footer ends -->`.
    # And prepend `sidebar_html` before it.
    # BUT, we only want to do this for videos that *had* the bad block?
    # No, all videos (except 1 & 2 which are already fixed) have the bad block AND need the sidebar.
    # Videos 1 & 2 do NOT have the bad block.
    # So if we strip bad_block from ALL videos.
    # Then we check ALL videos. If they lack a sidebar, we add it.
    
    updated_content = content.replace(bad_block, "")
    
    # Now, check for missing sidebars.
    # Pattern: `</div>\n\s*<!-- footer ends -->`
    # If a sidebar exists, it would be `</div>\n...videoSidebar...\n<!-- footer ends -->`
    # If sidebar is missing (because we didn't add it, or it wasn't there), we see `</div>` (videoFooter) followed immediately by `<!-- footer ends -->`.
    
    # Regex to find videoFooter closing followed by footer ends, WITHOUT sidebar in between.
    # We look for `</div>` followed by optional whitespace, then `<!-- footer ends -->`.
    # The `</div>` here is the one closing videoFooter.
    
    pattern_missing_sidebar = r'(</div>)(\s*)(<!-- footer ends -->)'
    
    def add_sidebar(match):
        # check if sidebar is already there?
        # The regex `(</div>)(\s*)(<!-- footer ends -->)` matches ONLY if there is strict adjacency (whitespace only).
        # If sidebar was there, there would be `<div class="videoSidebar">` in the whitespace, which \s* would NOT match.
        # So this is safe!
        
        closing_div = match.group(1)
        indent = match.group(2) # newlines and spaces
        footer_ends = match.group(3)
        return f"{closing_div}\n{sidebar_html}\n{indent}{footer_ends}"
        
    final_content = re.sub(pattern_missing_sidebar, add_sidebar, updated_content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print("Fixed HTML successfully.")

else:
    print("Could not find exact match for bad_block. Dumping snippet for debug.")
    # Debug snippet
    print(content[5000:6000]) # Arbitrary chunk
