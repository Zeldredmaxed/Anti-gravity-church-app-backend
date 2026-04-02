# 🚨 ACTION REQUIRED: Frontend UI/UX Stabilization & Bug Fixes

Hello Frontend Team!

The backend database transactions, privacy settings, and missing endpoint parameters have now been fully stabilized. We have resolved the silent database failures, and data scaling issues are fixed.

However, several UI features remain broken due to missing state bindings, incorrect prop mappings, or missing UI screens. Please implement the following fixes in the **React Native / Expo** application.

---

### 1. Shorts / Clips Visibility on User Profile
**The Issue:** Users cannot see the Shorts they uploaded when viewing their own profile, even though the upload was successful.
**The Fix:** 
The backend has been updated to accept an `author_id` parameter for clips. In the profile "Shorts" tab, fetch the user's specific shorts by calling:
```typescript
GET /api/v1/clips?author_id={user_id}
// Make sure to include Authorization: Bearer <token>
```
Render the resulting array in the profile grid.

### 2. Prevent Self-Following 
**The Issue:** The user can see a "Follow" button on their own posts and shorts.
**The Fix:**
The backend already rejects self-following with a `400 Bad Request`. To solve this visually, you MUST hide the "Follow" button anywhere content is displayed if the author is the currently logged-in user.
```tsx
{currentUser.id !== post.author.id && (
  <FollowButton targetUserId={post.author.id} />
)}
```

### 3. Admin Members Dashboard "Not Showing Anything"
**The Issue:** The analytics (total members, active prayers) are empty, and the "Members" list is empty.
**The Fix:** 
1. **Aggregates/Stats:** Ensure you are fetching from `GET /api/v1/dashboard/metrics` (Requires `admin` role). The JSON structure returned is:
   ```json
   {
     "members": { "total": 120, "trend": 5, "label": "new this month" },
     "giving": { "total": 5000.0, "trend": 10.5, "label": "vs last month" },
     "prayers": { "total": 12, "trend": 0, "label": "active" }
   }
   ```
   Ensure you are mapping `response.data.members.total`, not `response.data.total_members`.
2. **Members List:** To view members, ensure you are calling `GET /api/v1/members`. If the list is empty, verify the API request includes `Authorization: Bearer <token>` and that the user's role is `admin` or `pastor`.

### 4. Prayer Wall Comments Not Registering Typing
**The Issue:** When a user tries to type a comment on a prayer, nothing appears on the screen (infinite loading or blank).
**The Fix:**
This is a standard React Native controlled input error.
1. Check your `TextInput` for the comment box. Ensure `value` is bound to state and `onChangeText` is updating that state.
   ```tsx
   const [comment, setComment] = useState("");
   <TextInput value={comment} onChangeText={setComment} />
   ```
2. When submitting, ensure you call the newly stabilized backend endpoint:
   ```typescript
   POST /api/v1/prayers/{prayer_id}/responses
   Body: { "content": comment, "is_anonymous": false }
   ```

### 5. Bookmarks Navigation Routing Incorrectly
**The Issue:** When clicking on saved bookmarks, they all navigate to the same module (e.g., mail or music) regardless of what the bookmark actually is.
**The Fix:**
The bookmark API `GET /api/v1/social/saved` returns objects containing `item_type` (e.g., `"post"`, `"clip"`, `"song"`, `"event"`) and `item_id`.
You must use a `switch` statement on `item.item_type` to route the user to the correct screen:
```typescript
const handleBookmarkClick = (bookmark) => {
  switch(bookmark.item_type) {
    case 'post': router.push(`/feed/${bookmark.item_id}`); break;
    case 'clip': router.push(`/shorts/${bookmark.item_id}`); break;
    case 'song': router.push(`/music/${bookmark.item_id}`); break;
    // ... add others
    default: console.warn("Unknown bookmark type");
  }
}
```

### 6. Create Funds in Finance
**The Issue:** Admins need the ability to create separate funds (Tithes, Offerings, Building Fund, Vacation) so users can give towards them, but there is no UI for it.
**The Fix:**
The backend already supports this! Please build a "Create Fund" form in the admin finance section that submits to:
```typescript
POST /api/v1/funds
// Body:
{
  "name": "Building Fund",
  "description": "For the new sanctuary",
  "fund_type": "designated", // or 'general'
  "is_tax_deductible": true,
  "goal_amount": 50000.00
}
```
Users can then view these on the giving page by calling `GET /api/v1/funds` where `is_active=true`.

---
**Thank you! Reach out if you need clarification on the API contracts.**
