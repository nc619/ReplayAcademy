import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F


class Net(nn.Module):
    # Single layer MLP with n_features input and n_classes output + sigmoid classification
    def __init__(self, n_features, n_classes):
        super(Net, self).__init__()
        self.fc1 = nn.Linear(n_features, n_classes)

    def forward(self, x):
        x = self.fc1(x)
        x = F.sigmoid(x)
        return x


def train_model(model, train_loader, criterion, optimizer, num_epochs):
    for epoch in range(num_epochs):
        for inputs, labels in train_loader:
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()


def test_model(model, test_loader):
    with torch.no_grad():
        for inputs, labels in test_loader:
            outputs = model(inputs)
            predicted = (outputs > 0.5).float()
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
    return 100 * correct / total


def main():
    # Load data
    train_data = torch.load('train_data.pt')
    test_data = torch.load('test_data.pt')

    # Define model 
    model = Net(n_features=train_data.shape[1], n_classes=1)

    # Define loss function and optimizer
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # Train model
    train_model(model, train_data, criterion, optimizer, num_epochs=10)
    

