// Initialize Web3
let web3;
if (typeof window.ethereum !== 'undefined') {
    web3 = new Web3(window.ethereum);
    window.ethereum.request({ method: 'eth_requestAccounts' })
        .then(() => console.log('MetaMask connected'))
        .catch(error => console.error('User denied account access or there was an error:', error));
} else {
    const provider = new Web3.providers.HttpProvider('HTTP://192.168.1.4:7545'); // Adjust this URL as needed
    web3 = new Web3(provider);
}

// Replace with your actual contract address and ABI
const contractAddress = '0xFA4422dA49ac130925Ae4e5FCa54772D5b3b3897';
const contractABI = 
[
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "temperature",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "humidity",
				"type": "uint256"
			}
		],
		"name": "addReading",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "index",
				"type": "uint256"
			}
		],
		"name": "getReading",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "getTotalReadings",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"name": "readings",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "timestamp",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "temperature",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "humidity",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	}
];

const contract = new web3.eth.Contract(contractABI, contractAddress);

// Function to handle "View Readings" button click
async function viewReadings() {
    try {
        const accounts = await web3.eth.getAccounts();
        const account = accounts[0];
        
        await contract.methods.getTotalReadings().send({ from: account })
            .on('transactionHash', function(hash) {
                console.log('Transaction sent: ', hash);
            })
            .on('receipt', function(receipt) {
                console.log('Transaction confirmed: ', receipt);
                window.location.href = 'readings.html'; // Redirect to the readings page
            })
            .on('error', function(error) {
                console.error('Error sending transaction:', error);
            });
    } catch (error) {
        console.error('Error in viewReadings:', error);
    }
}
