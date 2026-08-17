// const { TwitterBot } = require('x-twitter-bot');

// async function postTweet(text) {
//     try {
//         const bot = new TwitterBot({
//             authToken: process.env.X_AUTH_TOKEN,
//             ct0: process.env.X_CT0
//         });
        
//         const result = await bot.tweet(text);
//         console.log(result.id);
        
//     } catch (error) {
//         console.error(error.message);
//         process.exit(1);
//     }
// }

// const text = process.argv.slice(2).join(' ');
// if (!text) {
//     console.error('No text provided');
//     process.exit(1);
// }

// postTweet(text);